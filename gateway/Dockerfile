FROM nginx:alpine

# UI files
COPY public/ /usr/share/nginx/html/

# Nginx template (envsubst will fill in PRODUCT_BASE/USER_BASE/ORDER_BASE)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
