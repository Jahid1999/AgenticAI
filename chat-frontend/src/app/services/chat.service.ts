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
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(private http: HttpClient) {}

  sendMessage(message: string): Observable<ChatResponse> {
    const request: ChatRequest = { message };

    return this.http.post<ChatResponse>(`${this.apiUrl}/message`, request).pipe(
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

  resetConversation(): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/reset`, {}).pipe(
      tap(() => this.clearMessages()),
      catchError(this.handleError)
    );
  }

  healthCheck(): Observable<{ status: string; service: string }> {
    return this.http.get<{ status: string; service: string }>(`${this.apiUrl}/health`).pipe(
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
