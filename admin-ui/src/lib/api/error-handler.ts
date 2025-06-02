/**
 * Utility for handling API errors, especially Pydantic validation errors
 */

export interface ValidationError {
    loc: (string | number)[];
    msg: string;
    type: string;
    input?: any;
}

export interface ApiErrorResponse {
    detail?: string | ValidationError[];
    message?: string;
    error?: string;
    statusCode?: number;
}

export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public details?: any
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Convert Pydantic validation errors to readable messages
 */
export function formatValidationErrors(errors: ValidationError[]): string {
    return errors
        .map((err) => {
            if (err.loc && err.msg) {
                const location = err.loc.join(' → ');
                return `${location}: ${err.msg}`;
            }
            return err.msg || 'Validation error';
        })
        .join(', ');
}

/**
 * Handle API response and extract error messages
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData: ApiErrorResponse = await response.json().catch(() => ({}));

        let errorMessage: string;

        // Handle Pydantic validation errors (422 status)
        if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
            errorMessage = formatValidationErrors(errorData.detail);
        } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
        } else if (errorData.message) {
            errorMessage = errorData.message;
        } else if (errorData.error) {
            errorMessage = errorData.error;
        } else {
            errorMessage = `API Error: ${response.statusText}`;
        }

        throw new ApiError(response.status, errorMessage, errorData);
    }

    return response.json();
}

/**
 * Extract error message from any error type
 */
export function getErrorMessage(error: unknown): string {
    if (error instanceof ApiError) {
        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    if (typeof error === 'string') {
        return error;
    }

    if (error && typeof error === 'object' && 'message' in error) {
        return String(error.message);
    }

    return 'An unexpected error occurred';
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): boolean {
    return error instanceof ApiError && error.status === 422;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
    return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

/**
 * Check if error is a not found error
 */
export function isNotFoundError(error: unknown): boolean {
    return error instanceof ApiError && error.status === 404;
}

/**
 * Check if error is a server error
 */
export function isServerError(error: unknown): boolean {
    return error instanceof ApiError && error.status >= 500;
} 