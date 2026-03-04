"""
Permission Diagnostic and Fix Script
Run this to diagnose and fix journalist permission issues
"""

import os
import django

# Setup Django
<<<<<<< HEAD
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_project.settings")
=======
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')
>>>>>>> docs
django.setup()

from news_app.models import CustomUser
from django.contrib.auth.models import Permission, Group
from news_app.utils import assign_user_to_group


def check_groups():
    """Check if groups exist"""
    print("=== CHECKING GROUPS ===")
    groups = Group.objects.all()
<<<<<<< HEAD

=======
    
>>>>>>> docs
    if groups.count() == 0:
        print("❌ NO GROUPS FOUND!")
        print("   Run: python manage.py setup_groups")
        return False
<<<<<<< HEAD

=======
    
>>>>>>> docs
    for group in groups:
        print(f"{group.name} exists")
        perm_count = group.permissions.count()
        print(f"   Permissions: {perm_count}")
        for perm in group.permissions.all():
            print(f"     - {perm.codename}")
<<<<<<< HEAD

=======
    
>>>>>>> docs
    return True


def check_permissions():
    """Check if required permissions exist"""
    print("\n=== CHECKING PERMISSIONS ===")
<<<<<<< HEAD

    required = [
        "add_article",
        "change_article",
        "delete_article",
        "view_article",
        "add_newsletter",
        "change_newsletter",
        "delete_newsletter",
        "view_newsletter",
    ]

    all_exist = True
    for codename in required:
        exists = Permission.objects.filter(
            codename=codename, content_type__app_label="news_app"
        ).exists()

=======
    
    required = [
        'add_article',
        'change_article',
        'delete_article',
        'view_article',
        'add_newsletter',
        'change_newsletter',
        'delete_newsletter',
        'view_newsletter',
    ]
    
    all_exist = True
    for codename in required:
        exists = Permission.objects.filter(
            codename=codename,
            content_type__app_label='news_app'
        ).exists()
        
>>>>>>> docs
        if exists:
            print(f"{codename}")
        else:
            print(f"{codename} MISSING!")
            all_exist = False
<<<<<<< HEAD

    if not all_exist:
        print("\nSome permissions missing!")
        print("   Run: python manage.py migrate")

=======
    
    if not all_exist:
        print("\nSome permissions missing!")
        print("   Run: python manage.py migrate")
    
>>>>>>> docs
    return all_exist


def check_users():
    """Check all users and their permissions"""
    print("\n=== CHECKING USERS ===")
<<<<<<< HEAD

    journalists = CustomUser.objects.filter(role="journalist")

    if journalists.count() == 0:
        print("No journalists found")
        return True

    for user in journalists:
        print(f"\n👤 {user.username} (role: {user.role})")

=======
    
    journalists = CustomUser.objects.filter(role='journalist')
    
    if journalists.count() == 0:
        print("No journalists found")
        return True
    
    for user in journalists:
        print(f"\n👤 {user.username} (role: {user.role})")
        
>>>>>>> docs
        # Check group membership
        groups = user.groups.all()
        if groups.count() == 0:
            print("   ❌ Not in any group!")
            print("   Fixing...")
            assign_user_to_group(user)
            print(" ✅ Fixed!")
        else:
            for group in groups:
                print(f"   ✅ In group: {group.name}")
<<<<<<< HEAD

        # Check key permissions
        can_add_article = user.has_perm("news_app.add_article")
        can_add_newsletter = user.has_perm("news_app.add_newsletter")

        print(f"   Can create articles: {'✅' if can_add_article else '❌'}")
        print(f"   Can create newsletters: {'✅' if can_add_newsletter else '❌'}")

        if not can_add_article or not can_add_newsletter:
            print("Missing permissions!")

=======
        
        # Check key permissions
        can_add_article = user.has_perm('news_app.add_article')
        can_add_newsletter = user.has_perm('news_app.add_newsletter')
        
        print(f"   Can create articles: {'✅' if can_add_article else '❌'}")
        print(f"   Can create newsletters: {'✅' if can_add_newsletter else '❌'}")
        
        if not can_add_article or not can_add_newsletter:
            print("Missing permissions!")
    
>>>>>>> docs
    return True


def fix_all_journalists():
    """Fix all journalist users"""
    print("\n=== FIXING ALL JOURNALISTS ===")
<<<<<<< HEAD

    journalists = CustomUser.objects.filter(role="journalist")

    for user in journalists:
        assign_user_to_group(user)
        print(f"Fixed {user.username}")

=======
    
    journalists = CustomUser.objects.filter(role='journalist')
    
    for user in journalists:
        assign_user_to_group(user)
        print(f"Fixed {user.username}")
    
>>>>>>> docs
    print(f"\nFixed {journalists.count()} journalists")


def main():
    print("╔════════════════════════════════════════╗")
    print("║  PERMISSION DIAGNOSTIC & FIX SCRIPT    ║")
    print("╚════════════════════════════════════════╝\n")
<<<<<<< HEAD

=======
    
>>>>>>> docs
    # Run checks
    groups_ok = check_groups()
    perms_ok = check_permissions()
    check_users()
<<<<<<< HEAD

=======
    
>>>>>>> docs
    # Offer to fix
    if not groups_ok:
        print("\n Please run: python manage.py setup_groups")
        return
<<<<<<< HEAD

    if not perms_ok:
        print("\nPlease run: python manage.py migrate")
        return

    print("\n" + "=" * 50)
    response = input("\nFix all journalist permissions? (y/n): ")

    if response.lower() == "y":
=======
    
    if not perms_ok:
        print("\nPlease run: python manage.py migrate")
        return
    
    print("\n" + "="*50)
    response = input("\nFix all journalist permissions? (y/n): ")
    
    if response.lower() == 'y':
>>>>>>> docs
        fix_all_journalists()
        print("\nALL DONE!")
        print("\nNow test:")
        print("1. Login as journalist")
        print("2. Go to /articles/create/")
        print("3. Should work!")
    else:
        print("\nNo changes made")


<<<<<<< HEAD
if __name__ == "__main__":
    main()
=======
if __name__ == '__main__':
    main()
>>>>>>> docs
