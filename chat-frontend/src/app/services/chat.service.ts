import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { ChatRequest, ChatResponse, ChatMessage } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiUrl = '/api/chat';
  private readonly SESSION_KEY = 'chat_session_id';

  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  private sessionId: string | null = null;

  constructor(private http: HttpClient) {
    // Restore session from localStorage if exists
    this.sessionId = localStorage.getItem(this.SESSION_KEY);
  }

  sendMessage(message: string): Observable<ChatResponse> {
    const request: ChatRequest = {
      message,
      session_id: this.sessionId || undefined
    };

    return this.http.post<ChatResponse>(`${this.apiUrl}/message`, request).pipe(
      tap(response => {
        // Store session ID for future requests
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
