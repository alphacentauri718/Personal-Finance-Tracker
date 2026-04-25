def calculate_net_worth(user_id: int):
    
    total_assets = sum(a.value for a in db.query(Asset).filter(Asset.user_id == user_id).all())

    total_expenses = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == user_id).all())

    return total_assets - total_expenses