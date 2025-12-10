import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../services/chat.service';
import { ChatMessage } from '../../models/chat.model';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild('messageInput') private messageInput!: ElementRef;

  messages: ChatMessage[] = [];
  newMessage = '';
  isLoading = false;
  isConnected = false;
  connectionError = '';

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.chatService.messages$.subscribe(messages => {
      this.messages = messages;
    });
    this.checkConnection();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  async checkConnection(): Promise<void> {
    this.chatService.healthCheck().subscribe({
      next: () => {
        this.isConnected = true;
        this.connectionError = '';
      },
      error: (error) => {
        this.isConnected = false;
        this.connectionError = 'Unable to connect to the chat server. Please ensure the backend is running.';
      }
    });
  }

  sendMessage(): void {
    const message = this.newMessage.trim();
    if (!message || this.isLoading) return;

    const userMessage: ChatMessage = {
      id: this.chatService.generateId(),
      content: message,
      role: 'user',
      timestamp: new Date()
    };

    this.chatService.addMessage(userMessage);
    this.newMessage = '';
    this.isLoading = true;

    const loadingMessage: ChatMessage = {
      id: this.chatService.generateId(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };
    this.chatService.addMessage(loadingMessage);

    this.chatService.sendMessage(message).subscribe({
      next: (response) => {
        this.chatService.updateLastMessage({
          content: response.response,
          agentUsed: response.agent_used,
          isLoading: false
        });
        this.isLoading = false;
        this.focusInput();
      },
      error: (error) => {
        this.chatService.updateLastMessage({
          content: `Error: ${error.message}`,
          isLoading: false
        });
        this.isLoading = false;
        this.focusInput();
      }
    });
  }

  clearChat(): void {
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
