# AI Usage

I used ChatGPT (GPT) as an AI-assisted development and learning tool throughout the development of the Trade Recorder & PnL Service.

## 1. Understanding the Requirements

- Initially, I used ChatGPT to understand the complete assignment and break down the requirements into smaller, manageable tasks.
- Discussed the expected functionality, including trade ingestion, input validation, idempotency, position tracking, PnL calculation, oversell protection, and trade reconciliation.
- Asked for explanations of technical concepts and terminology to understand what each requirement meant and why it was needed.

## 2. Discussing and Finalizing the Approach

- Discussed different ways to structure the application and organize its components.
- Explored possible approaches for database design, API development, trade processing, and position management.
- Discussed FIFO and Weighted Average cost-basis methods, compared their calculations, and finalized the approach for supporting both methods.
- Discussed how to handle duplicate trades, conflicting requests, invalid inputs, and overselling.
- Finalized the overall implementation approach based on the assignment requirements and the discussions.

## 3. Implementation Assistance

During development, I used ChatGPT to understand and work through the implementation of individual features, including:

- Trade ingestion and input validation.
- Idempotency using the combination of venue and trade ID.
- Updating positions after BUY and SELL trades.
- Calculating average cost and realized PnL.
- Calculating unrealized and total PnL using the latest market price.
- Implementing FIFO and Weighted Average cost-basis calculations.
- Preventing overselling without changing the existing position.
- Reconciling application trades with venue-provided records to identify missing, extra, and mismatched trades.

I also discussed code structure, implementation choices, error handling, and potential edge cases with ChatGPT to improve my understanding of the solution.

## 4. Testing and Debugging

- Used ChatGPT to understand how to create and run automated tests using pytest.
- Discussed test scenarios for normal operations, duplicate trades, conflicting duplicates, invalid inputs, overselling, PnL calculations, and reconciliation.
- Used AI assistance to investigate errors, understand unexpected responses, and identify possible improvements.
- Performed manual API testing through FastAPI Swagger UI.
- Tested concurrent duplicate requests to verify that a trade was not processed more than once.

## 5. Documentation Assistance

Used ChatGPT to help prepare and improve the project documentation files.

## 6. Verification and Responsibility

AI-generated explanations and suggestions were used as guidance during development. I reviewed and adapted the approaches to the project, executed the application, ran the automated tests, and verified the API behavior through manual testing.