FROM nginx:1.25

# Delete the default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our new config
COPY default.conf /etc/nginx/conf.d