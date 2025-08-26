import { http } from '../lib/http';

interface TestSolveResponse {
  request_id: string | null;
  result: string;
  model: string;
  duration_ms: number;
  is_test: boolean;
}

export const testSolveService = {
  async solveImage(file: File): Promise<TestSolveResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await http.post('/customers/test-solve', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return data;
  },
};
