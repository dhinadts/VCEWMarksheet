export type UserRole = "ADMIN" | "PROFESSOR" | "STUDENT";
export type SessionUser = { id: string; username: string; email: string | null; user_type: UserRole; must_change_password: boolean };
export type ApiSuccess<T> = { success: true; data: T; message: string };
export type PageData<T> = { items: T[]; page: number; page_size: number; total: number; total_pages: number };
export type RecordRow = Record<string, string | number | boolean | null> & { id: string };
