from typing import List, Dict, Set

# «Каталог» и «пользователи» пока в памяти
catalog: List[Dict[str, str]] = [
    {"id": "14pro256",  "name": "iPhone 14 Pro 256 GB",  "price": "₽ 109 990"},
    {"id": "14pro128",  "name": "iPhone 14 Pro 128 GB",  "price": "₽ 99 990"},
    {"id": "13mini128", "name": "iPhone 13 mini 128 GB","price": "₽ 69 990"},
]

users: Set[int] = set()
