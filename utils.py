import bcrypt

CATEGORY_KEYWORDS = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "coffee", "burger", "pizza", "lunch", "dinner", "groceries", "supermarket"],
    "Transportation": ["uber", "ola", "metro", "fuel", "petrol", "diesel", "bus", "train", "flight", "parking"],
    "Utilities & Bills": ["electricity", "water", "internet", "wifi", "recharge", "mobile", "gas", "broadband", "rent"],
    "Entertainment": ["netflix", "spotify", "movie", "cinema", "game", "prime", "concert", "hotstar"],
    "Shopping": ["amazon", "flipkart", "myntra", "clothes", "shoes", "electronics", "mall"],
    "Healthcare": ["pharmacy", "doctor", "hospital", "medicine", "clinic", "dental", "gym"],
    "Education": ["course", "book", "udemy", "tuition", "college", "exam", "stationery"]
}

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def auto_categorize(description: str, default_category: str = "Other") -> str:
    if not description:
        return default_category
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
    return default_category
