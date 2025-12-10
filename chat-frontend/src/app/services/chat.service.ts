import { Injectable, NgZone } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject, Subject } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { ChatRequest, ChatResponse, ChatMessage } from '../models/chat.model';

export interface StreamEvent {
  type: 'session' | 'agent' | 'content' | 'done' | 'error';
  session_id?: string;
  agent?: string;
  content?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiUrl = '/api/chat';
  private readonly SESSION_KEY = 'chat_session_id';

  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  private sessionId: string | null = null;
  private abortController: AbortController | null = null;

  constructor(
    private http: HttpClient,
    private ngZone: NgZone
  ) {
    this.sessionId = localStorage.getItem(this.SESSION_KEY);
  }

  /**
   * Send a message with streaming response using fetch API.
   */
  sendMessageStream(message: string): Observable<StreamEvent> {
    const subject = new Subject<StreamEvent>();

    // Cancel any existing request
    if (this.abortController) {
      this.abortController.abort();
    }
    this.abortController = new AbortController();

    const body = JSON.stringify({
      message,
      session_id: this.sessionId || undefined
    });

    fetch(`${this.apiUrl}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body,
      signal: this.abortController.signal,
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No reader available');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6).trim();
              if (jsonStr) {
                try {
                  const event: StreamEvent = JSON.parse(jsonStr);

                  this.ngZone.run(() => {
                    // Update session ID if received
                    if (event.type === 'session' && event.session_id) {
                      this.sessionId = event.session_id;
                      localStorage.setItem(this.SESSION_KEY, event.session_id);
                    }

                    subject.next(event);

                    if (event.type === 'done' || event.type === 'error') {
                      subject.complete();
                    }
                  });
                } catch (e) {
                  console.error('Error parsing SSE data:', e, jsonStr);
                }
              }
            }
          }
        }

        this.ngZone.run(() => subject.complete());
      })
      .catch(error => {
        if (error.name === 'AbortError') {
          this.ngZone.run(() => subject.complete());
        } else {
          console.error('Fetch error:', error);
          this.ngZone.run(() => subject.error(error));
        }
      });

    return subject.asObservable();
  }

  /**
   * Cancel ongoing stream request.
   */
  cancelStream(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Send a message without streaming (fallback).
   */
  sendMessage(message: string): Observable<ChatResponse> {
    const request: ChatRequest = {
      message,
      session_id: this.sessionId || undefined
    };

    return this.http.post<ChatResponse>(`${this.apiUrl}/message`, request).pipe(
      tap(response => {
        if (response.session_id) {
          this.sessionId = response.session_id;
          localStorage.setItem(this.SESSION_KEY, response.session_id);
        }
      }),
      catchError(this.handleError)
    );
  }

  addMessage(message: ChatMessage): void {
    const currentMessages = this.messagesSubject.getValue();
    this.messagesSubject.next([...currentMessages, message]);
  }

  updateLastMessage(updates: Partial<ChatMessage>): void {
    const currentMessages = this.messagesSubject.getValue();
    if (currentMessages.length > 0) {
      const lastIndex = currentMessages.length - 1;
      currentMessages[lastIndex] = { ...currentMessages[lastIndex], ...updates };
      this.messagesSubject.next([...currentMessages]);
    }
  }

  private typewriterQueue: string[] = [];
  private isTypewriting = false;
  private typewriterSpeed = 10; // ms per character

  appendToLastMessage(content: string): void {
    // Add to queue for typewriter effect
    this.typewriterQueue.push(content);
    this.processTypewriterQueue();
  }

  private async processTypewriterQueue(): Promise<void> {
    if (this.isTypewriting || this.typewriterQueue.length === 0) {
      return;
    }

    this.isTypewriting = true;

    while (this.typewriterQueue.length > 0) {
      const content = this.typewriterQueue.shift()!;

      // If content is small (< 50 chars), add directly for smoother experience
      if (content.length < 50) {
        this.appendContentDirect(content);
      } else {
        // For larger chunks, use typewriter effect
        await this.typewriteContent(content);
      }
    }

    this.isTypewriting = false;
  }

  private appendContentDirect(content: string): void {
    const currentMessages = this.messagesSubject.getValue();
    if (currentMessages.length > 0) {
      const lastIndex = currentMessages.length - 1;
      const lastMessage = currentMessages[lastIndex];
      currentMessages[lastIndex] = {
        ...lastMessage,
        content: (lastMessage.content || '') + content
      };
      this.messagesSubject.next([...currentMessages]);
    }
  }

  private async typewriteContent(content: string): Promise<void> {
    // Split into chunks for smoother rendering
    const chunkSize = 5; // characters per chunk
    for (let i = 0; i < content.length; i += chunkSize) {
      const chunk = content.slice(i, i + chunkSize);
      this.ngZone.run(() => this.appendContentDirect(chunk));
      await this.sleep(this.typewriterSpeed);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  isStreaming(): boolean {
    return this.isTypewriting || this.typewriterQueue.length > 0;
  }

  clearTypewriterQueue(): void {
    this.typewriterQueue = [];
    this.isTypewriting = false;
  }

  getMessages(): ChatMessage[] {
    return this.messagesSubject.getValue();
  }

  clearMessages(): void {
    this.messagesSubject.next([]);
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  resetConversation(): Observable<{ status: string; message: string }> {
    const sessionId = this.sessionId;
    return this.http.post<{ status: string; message: string }>(
      `${this.apiUrl}/reset`,
      null,
      { params: sessionId ? { session_id: sessionId } : {} }
    ).pipe(
      tap(() => {
        this.clearMessages();
        this.sessionId = null;
        localStorage.removeItem(this.SESSION_KEY);
      }),
      catchError(this.handleError)
    );
  }

  createNewSession(): Observable<{ session_id: string; message: string }> {
    return this.http.post<{ session_id: string; message: string }>(
      `${this.apiUrl}/session/new`,
      {}
    ).pipe(
      tap(response => {
        this.sessionId = response.session_id;
        localStorage.setItem(this.SESSION_KEY, response.session_id);
        this.clearMessages();
      }),
      catchError(this.handleError)
    );
  }

  healthCheck(): Observable<{ status: string; service: string; active_sessions: number }> {
    return this.http.get<{ status: string; service: string; active_sessions: number }>(
      `${this.apiUrl}/health`
    ).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = error.error?.detail || `Server error: ${error.status}`;
    }

    console.error('Chat service error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}
