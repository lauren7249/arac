FROM nginx

RUN ln -sf /dev/stdout /var/log/nginx/advisorconnect.log
RUN ln -sf /dev/stderr /var/log/nginx/advisorconnect.err

COPY default.conf /etc/nginx/conf.d/default.conf
