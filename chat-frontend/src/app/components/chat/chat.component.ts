import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ChatService, StreamEvent } from '../../services/chat.service';
import { ChatMessage } from '../../models/chat.model';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild('messageInput') private messageInput!: ElementRef;

  messages: ChatMessage[] = [];
  newMessage = '';
  isLoading = false;
  isStreaming = false;
  isConnected = false;
  connectionError = '';
  currentAgent = '';

  private messagesSubscription?: Subscription;
  private streamSubscription?: Subscription;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.messagesSubscription = this.chatService.messages$.subscribe(messages => {
      this.messages = messages;
    });
    this.checkConnection();
  }

  ngOnDestroy(): void {
    this.messagesSubscription?.unsubscribe();
    this.streamSubscription?.unsubscribe();
    this.chatService.cancelStream();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  checkConnection(): void {
    this.chatService.healthCheck().subscribe({
      next: () => {
        this.isConnected = true;
        this.connectionError = '';
      },
      error: () => {
        this.isConnected = false;
        this.connectionError = 'Unable to connect to the chat server. Please ensure the backend is running.';
      }
    });
  }

  sendMessage(): void {
    const message = this.newMessage.trim();
    if (!message || this.isLoading || this.isStreaming) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: this.chatService.generateId(),
      content: message,
      role: 'user',
      timestamp: new Date()
    };
    this.chatService.addMessage(userMessage);
    this.newMessage = '';

    // Add empty assistant message for streaming
    const assistantMessage: ChatMessage = {
      id: this.chatService.generateId(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };
    this.chatService.addMessage(assistantMessage);

    this.isLoading = true;
    this.isStreaming = true;
    this.currentAgent = '';

    // Use streaming endpoint
    this.streamSubscription = this.chatService.sendMessageStream(message).subscribe({
      next: (event: StreamEvent) => {
        this.handleStreamEvent(event);
      },
      error: (error) => {
        this.chatService.updateLastMessage({
          content: `Error: ${error.message}`,
          isLoading: false
        });
        this.isLoading = false;
        this.isStreaming = false;
        this.focusInput();
      },
      complete: () => {
        this.chatService.updateLastMessage({ isLoading: false });
        this.isLoading = false;
        this.isStreaming = false;
        this.focusInput();
      }
    });
  }

  private handleStreamEvent(event: StreamEvent): void {
    switch (event.type) {
      case 'session':
        // Session ID is handled by the service
        break;

      case 'agent':
        this.currentAgent = event.agent || '';
        this.chatService.updateLastMessage({
          agentUsed: this.currentAgent
        });
        break;

      case 'content':
        if (event.content) {
          this.chatService.appendToLastMessage(event.content);
        }
        break;

      case 'done':
        this.chatService.updateLastMessage({
          agentUsed: event.agent || this.currentAgent,
          isLoading: false
        });
        break;

      case 'error':
        this.chatService.updateLastMessage({
          content: `Error: ${event.error}`,
          isLoading: false
        });
        break;
    }
  }

  clearChat(): void {
    this.streamSubscription?.unsubscribe();
    this.chatService.cancelStream();
    this.chatService.clearTypewriterQueue();
    this.isStreaming = false;
    this.isLoading = false;

    this.chatService.resetConversation().subscribe({
      next: () => {
        this.focusInput();
      },
      error: () => {
        this.chatService.clearMessages();
        this.focusInput();
      }
    });
  }

  handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  private focusInput(): void {
    setTimeout(() => {
      if (this.messageInput) {
        this.messageInput.nativeElement.focus();
      }
    }, 100);
  }

  getAgentIcon(agent: string | undefined): string {
    if (!agent) return '🤖';
    const lowerAgent = agent.toLowerCase();
    if (lowerAgent.includes('technical')) return '💻';
    if (lowerAgent.includes('student')) return '📚';
    if (lowerAgent.includes('general')) return '💬';
    return '🤖';
  }

  getAgentLabel(agent: string | undefined): string {
    if (!agent) return 'AI Assistant';
    return agent;
  }

  formatTime(date: Date): string {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }
}
