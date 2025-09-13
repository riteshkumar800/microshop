FROM nginx:1.25-alpine

# envsubst + certificates for HTTPS
RUN apk add --no-cache gettext ca-certificates

# Static page
COPY index.html /usr/share/nginx/html/index.html

# Nginx template that uses env vars
COPY nginx-cloud.tmpl /etc/nginx/templates/default.conf.template

# Render the template from env and boot nginx
CMD sh -c 'envsubst < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g "daemon off;"'
