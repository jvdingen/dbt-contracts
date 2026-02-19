select
    customer_id,
    total_payments,
    last_payment_date
from {{ source('payments', 'payments') }}
