FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -qO- http://localhost/ || exit 1