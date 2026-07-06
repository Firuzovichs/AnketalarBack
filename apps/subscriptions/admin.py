from django.contrib import admin
from .models import Plan, UserSubscription, ApplePurchase

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['plan_type', 'name', 'price_monthly', 'likes_per_day', 'chat_duration_days', 'apple_product_id', 'can_see_who_liked', 'can_boost_profile']
    list_editable = ['chat_duration_days', 'apple_product_id']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'started_at', 'expires_at', 'is_active', 'apple_original_transaction_id']
    search_fields = ['user__email', 'user__phone', 'apple_original_transaction_id']
    autocomplete_fields = ['user']


# MUHIM: bu — Apple to'lovlari bo'yicha APPEND-ONLY audit jurnali. Loyihaning
# umumiy qoidasiga ko'ra (qarang apps/users/admin.py, apps/chat/admin.py dagi
# bir xil konvensiya) bazadan hech narsa butunlay o'chirilmasin — shu sababli
# bu yerda "Delete" har doim o'chirib qo'yilgan va qatorlar hech qachon
# tahrirlanmaydi (faqat VerifyPurchaseView/AppleServerNotificationView orqali
# yangi qatorlar qo'shiladi).
@admin.register(ApplePurchase)
class ApplePurchaseAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'source', 'notification_type', 'product_id', 'environment', 'is_valid', 'expires_at']
    list_filter = ['source', 'is_valid', 'environment', 'notification_type']
    search_fields = ['user__email', 'user__phone', 'product_id', 'original_transaction_id', 'transaction_id']
    autocomplete_fields = ['user']
    ordering = ['-created_at']
    readonly_fields = [f.name for f in ApplePurchase._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        # Qatorlar faqat backend tomonidan (xarid tasdiqlash/Apple bildirishnomasi
        # kelganda) avtomatik yaratiladi — admin paneldan qo'lda qo'shilmaydi.
        return False

    def has_change_permission(self, request, obj=None):
        return False
