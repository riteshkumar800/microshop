FROM nginx:alpine

# Static UI
COPY public/ /usr/share/nginx/html/

# Render’s nginx image auto-renders any file in /etc/nginx/templates/*.template
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Launch nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
