# Math Solver Implementation

## Overview

The image solve endpoint has been updated to specifically handle mathematical problems in images. The system can extract math problems from images and return numerical answers.

## Key Changes

### 1. Math-Specific Prompt

The OpenAI client now uses a specialized prompt designed for mathematical problem solving:

- Identifies mathematical problems or expressions in images
- Solves them step by step
- Returns only the final numerical answer
- Handles various types of math problems:
  - Basic arithmetic (addition, subtraction, multiplication, division)
  - Exponents and roots
  - Percentages
  - Word problems
  - Multiple problems in one image

### 2. Dual Implementation Architecture

The system now supports two modes of operation:

#### Mock Mode (Default)
- Used for development and testing
- No OpenAI API key required
- Returns realistic math answers from a predefined set
- Simulates different scenarios based on image size
- Always available (ping always returns true)

#### Production Mode
- Uses actual OpenAI Vision API
- Requires valid `OPENAI_API_KEY`
- Uses GPT-4 Vision model by default
- Temperature set to 0 for deterministic math results
- High detail image analysis for better OCR

### 3. Environment Configuration

New environment variable:
```bash
USE_MOCK_OPENAI=true  # Set to 'false' for production mode
```

Existing variables still used:
- `OPENAI_API_KEY`: Required for production mode
- `OPENAI_MODEL`: Model to use (defaults to gpt-vision, overridden to gpt-4-vision-preview in production)
- `OPENAI_TIMEOUT_S`: Request timeout in seconds

## API Response Format

### Success Response
```json
{
    "request_id": "uuid-here",
    "result": "42",  // Just the numerical answer
    "model": "gpt-vision",
    "duration_ms": 1234
}
```

### Error Cases
- If no math problem is found: `"result": "ERROR: No math problem found"`
- API errors maintain the same error response format

## Implementation Details

### Class Structure

1. **BaseOpenAIClient** (Abstract)
   - Defines the interface for all implementations
   - Methods: `solve_image()`, `ping()`

2. **MockOpenAIClient**
   - Implements mock functionality
   - Returns random answers from predefined problems
   - Simulates usage metrics

3. **ProductionOpenAIClient**
   - Implements actual OpenAI API calls
   - Uses specialized math prompt
   - Handles all error cases

4. **OpenAIClient** (Facade)
   - Singleton instance used throughout the app
   - Automatically selects implementation based on `USE_MOCK_OPENAI`
   - Transparent switching between modes

### Mock Problems Examples

The mock implementation includes various math problems:
- Basic: "2 + 2" → "4"
- Subtraction: "10 - 3" → "7"
- Multiplication: "5 × 6" → "30"
- Division: "100 ÷ 4" → "25"
- Exponents: "3² + 4²" → "25"
- Roots: "√144" → "12"
- Percentages: "15% of 200" → "30"
- Complex: "123 + 456" → "579"

## Testing

### Unit Testing
Use the provided test script:
```bash
uv run python test_math_solver.py
```

### API Testing
Test with curl (requires API token):
```bash
# Create a test image with a math problem
echo "5 + 3" > math.txt
convert -size 200x100 xc:white -font Arial -pointsize 30 \
        -draw "text 50,50 '5 + 3'" math.png

# Send to API (replace with actual token)
curl -X POST http://localhost:8000/api/core/solve \
     -H "Authorization: Bearer tok_your_token_here" \
     -F "file=@math.png"
```

## Switching to Production Mode

1. Set environment variable:
   ```bash
   USE_MOCK_OPENAI=false
   ```

2. Provide OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

3. Restart the server

## Error Handling

The system handles various error scenarios:

1. **No API Key in Production Mode**: Raises ValueError with helpful message
2. **Small/Invalid Images**: Returns "ERROR: No math problem found"
3. **API Timeouts**: Returns appropriate error with timeout code
4. **Network Errors**: Handles connection issues gracefully
5. **Invalid API Responses**: Catches and reports malformed responses

## Performance Considerations

- **Mock Mode**: Instant responses, no external API calls
- **Production Mode**: 
  - Uses high detail for better OCR accuracy
  - Temperature set to 0 for consistent results
  - Max tokens limited to 100 (math answers are short)
  - Configurable timeout (default 30 seconds)

## Billing

- All requests (successful or failed) are logged and billed
- Cost per request configurable via `COST_PER_REQUEST_CENTS`
- Usage metrics tracked in both modes
- Mock mode simulates realistic token usage
