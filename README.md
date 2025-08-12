# SmartSpend

SmartSpend is a personal finance web app that helps users track expenses, manage savings goals, and view monthly spending summaries with a clean, user-friendly interface.

## Design and Implementation

### Use of Object-Oriented Programming (OOP)

The backend of SmartSpend is implemented using Python classes to encapsulate key entities and their behaviors:

- **User**: Represents the user with attributes like email and password, and methods to save and update user data.
- **Income**: Encapsulates yearly, monthly, and weekly income data with methods to save and update income records.
- **Expense**: Represents individual expense entries with attributes such as amount, date, description, and category, along with methods to save, update, and delete expenses.
- **Goal**: Represents saving goals with attributes for name, target amount, and status, and methods to manage goals including activation, updating, and deletion.
- **DatabaseManager**: Handles database connections and initialization, abstracting SQLite operations.

This design applies OOP principles such as encapsulation and abstraction to organize code logically, improve maintainability, and promote code reuse.

### Data Types and Data Structures

- **Data Types**: The application uses appropriate data types including integers, floats, strings, booleans, and datetime objects to represent various data accurately.
- **Data Structures**: Lists and dictionaries are used to manage collections of categories, keywords, and query results efficiently.
- **Data Sources**: SQLite is used as the persistent data source, providing a lightweight and reliable database solution suitable for this application.

### Rationale for Choices

- **Classes and OOP**: Using classes allows grouping related data and behaviors, making the codebase easier to understand and extend.
- **SQLite Database**: Chosen for its simplicity and ease of integration with Python, suitable for a personal finance app.
- **Data Structures**: Lists and dictionaries provide efficient lookups and grouping, essential for categorizing expenses and managing keywords.


