/**
 * Handle API errors with special handling for email verification
 */
export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  isEmailNotVerified?: boolean;
}

export async function handleApiError(response: Response): Promise<ApiError> {
  const status = response.status;
  const contentType = response.headers.get('content-type');
  
  let message = 'An error occurred';
  let detail: string | undefined;
  let isEmailNotVerified = false;

  if (contentType?.includes('application/json')) {
    try {
      const data = await response.json();
      detail = data.detail || data.message;
      message = detail || 'An error occurred';
      
      // Check if this is email verification error
      if (status === 403 && detail?.includes('verify your email')) {
        isEmailNotVerified = true;
      }
    } catch {
      message = await response.text();
    }
  } else {
    message = await response.text();
  }

  return {
    status,
    message,
    detail,
    isEmailNotVerified,
  };
}

export function getErrorMessage(error: unknown): string {
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  return 'Unknown error occurred';
}
