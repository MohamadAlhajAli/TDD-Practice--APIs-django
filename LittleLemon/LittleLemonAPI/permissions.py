def get_user_role(user):
    if not user.is_authenticated:
        return "Anonymous"

    if user.is_superuser or user.groups.filter(name="Manager").exists():
        return "Manager"

    if user.groups.filter(name="Delivery crew").exists():
        return "Delivery crew"

    return "Customer"