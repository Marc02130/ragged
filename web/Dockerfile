# Placeholder until slice 7 (Webpack production build). Serves a static
# index and proxies /api via nginx.conf so compose boots on :8080.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY placeholder/index.html /usr/share/nginx/html/index.html
COPY public/ragged.png /usr/share/nginx/html/ragged.png
