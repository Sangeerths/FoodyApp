from functools import wraps
from django.shortcuts import redirect

def customer_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        customer_id = request.session.get('customer_id')
        if not customer_id:
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view