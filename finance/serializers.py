from rest_framework import serializers

class CheckoutRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    request_id = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
