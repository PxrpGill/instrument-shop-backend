---
name: brainstorm
description: Adaptive dialog loop to gather context and requirements before creating a plan in .opencode/plans/
---

# Brainstorm Skill

## Trigger
Automatically invoked when user describes a task that requires creating a plan in `.opencode/plans/`.

## Purpose
Collect all necessary context through adaptive dialog before designing a solution.

## Adaptive Dialog Loop

### Information Gathering Criteria
Agent continues asking questions until it fully understands:

1. **What** — concrete expected outcome
2. **Why** — business reason or problem being solved
3. **Context** — how this fits into the system
4. **Constraints** — technical, temporal, assumptions
5. **Success** — how completion will be measured

### Question Categories

**Core questions (use adaptively):**
- What should the result look like?
- What data is involved?
- Where does the data come from and where does it go?
- What can go wrong?
- Are there similar patterns in the codebase?
- What are the constraints and dependencies?

**Context questions (based on task type):**
- Who will use this?
- What permissions are needed?
- Should this be sync or async?
- Are there existing similar endpoints/services?
- What happens with invalid input?

**Edge case questions (for complex tasks):**
- What about empty states?
- What about large datasets?
- What about concurrent access?
- What about errors and retries?

### Decision Rules

1. **Simple task** (adding a field, minor fix) → 1-2 questions
2. **Medium task** (new endpoint, service) → 3-5 questions
3. **Complex task** (new module, architectural change) → As many as needed, up to ~7

**Stop condition:**
- All 5 criteria satisfied
- OR user says "足够了" / "enough" / "давай план"

**Never ask everything at once:**
- Start with 1-2 most critical questions
- Based on answers, determine what to ask next
- Let the conversation flow naturally

### Example Dialog Flow

```
User: хочу добавить экспорт заказов в CSV

Agent: Какие поля должны быть в CSV? (What)
User: номер заказа, дата, клиент, сумма, статус

Agent: Кто будет выгружать — клиенты или менеджеры? (Context: permissions)
User: менеджеры

Agent: Нужна фильтрация по датам или статусу?
User: да, по дате и статусу

Agent: Сколько записей может быть в выгрузке?
User: до 10 000

→ Agent has enough context, moves to code research and planning
```

## Output Format

After brainstorm, agent builds internal context stored in memory:

```
## Brainstorm Result

### Context
- Задача: экспорт заказов в CSV
- Пользователи: менеджеры
- Данные: заказ, дата, клиент, сумма, статус
- Фильтрация: по дате и статусу
- Объём: до 10 000 записей

### Decisions
- Staff-only endpoint
- Фильтрация по дате и статусу
- Потокобезопасная генерация

### Open Questions
- Нужен ли pagination в выгрузке?
- Какой формат даты?

### Areas to Research
- Существующие endpoint для заказов
- Как формируется CSV в проекте
- Пермишены staff
```

## Integration

After brainstorm completes:
1. If code research needed → explore relevant files
2. Create plan in `.opencode/plans/<task-name>.md`
3. Use brainstorm context in plan formation

## Principles

- Questions should feel like natural conversation, not interrogation
- Respect user's time — don't ask obvious things
- Use project conventions when asking (e.g., "Есть ли similar паттерн в apps/orders/")
- If user seems uncertain, help them think through it
- When enough context gathered, explicitly say so and move forward