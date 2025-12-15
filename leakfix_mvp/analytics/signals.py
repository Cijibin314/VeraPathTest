from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Practice, Provider, Referral, Invoice, AuditLog
from .middleware import get_current_user

def get_changed_fields(instance, old_instance):
    """
    Compare two model instances and return a dictionary of changed fields.
    """
    changed_fields = {}
    for field in instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name)
        new_value = getattr(instance, field_name)
        if old_value != new_value:
            changed_fields[field_name] = (old_value, new_value)
    return changed_fields

@receiver(pre_save, sender=Practice)
@receiver(pre_save, sender=Provider)
@receiver(pre_save, sender=Referral)
@receiver(pre_save, sender=Invoice)
def store_old_instance(sender, instance, **kwargs):
    """
    Store the old instance of the model on the instance itself before it's saved.
    """
    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_instance = None

@receiver(post_save, sender=Practice)
@receiver(post_save, sender=Provider)
@receiver(post_save, sender=Referral)
@receiver(post_save, sender=Invoice)
def log_save(sender, instance, created, **kwargs):
    """
    Log when a Practice, Provider, Referral, or Invoice is created or updated.
    """
    user = get_current_user()
    action = 'created' if created else 'updated'
    details = f"{sender.__name__} '{instance}' was {action}."

    if not created and hasattr(instance, '_old_instance') and instance._old_instance is not None:
        changed_fields = get_changed_fields(instance, instance._old_instance)
        if changed_fields:
            changes_summary = []
            for field, (old, new) in changed_fields.items():
                changes_summary.append(f"'{field}' changed from '{old}' to '{new}'")
            details += " Changes: " + "; ".join(changes_summary) + "."

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        target=f"{sender.__name__} {instance.pk}",
        details=details
    )

@receiver(post_delete, sender=Practice)
@receiver(post_delete, sender=Provider)
@receiver(post_delete, sender=Referral)
@receiver(post_delete, sender=Invoice)
def log_delete(sender, instance, **kwargs):
    """
    Log when a Practice, Provider, Referral, or Invoice is deleted.
    """
    user = get_current_user()
    
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action='deleted',
        target=f"{sender.__name__} {instance.pk}",
        details=f"{sender.__name__} '{instance}' was deleted."
    )
