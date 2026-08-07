# Pull base image.
FROM jlesage/baseimage-gui:ubuntu-26.04-v4

# Add TARGETARCH for multi-arch builds
ARG TARGETARCH

# Install packages
RUN upg-pkg && \
    add-pkg apt-utils nano libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libgbm-dev libxss1 libasound2t64 wget xterm libnss3 locales xdotool xclip ca-certificates libgl1 lsb-release \
    at-spi2-core python3-pyatspi xkb-data python3-rich && \
    # Install Node.js and NPM for non-x86 architectures to run Electron natively
    if [ "$TARGETARCH" != "amd64" ]; then \
        add-pkg nodejs npm && \
        npm install -g electron --unsafe-perm=true --allow-root; \
    fi && \
    locale-gen de_DE.UTF-8

# Generate and install favicons.
# alternative logo: https://breitbandmessung.de/images/breitbandmessung-logo.png
RUN APP_ICON_URL=https://www.breitbandmessung.de/public/images/appicon-512.png && \
    install_app_icon.sh "$APP_ICON_URL"

# Add files.
COPY rootfs/ /

# Fix permissions and line endings.
RUN find /etc/services.d -type f -name "*.dep" -exec chmod 644 {} + && \
    find /etc/services.d -type f -name "run" -exec chmod 755 {} + && \
    find /etc/services.d -type f -exec sed -i 's/\r$//' {} + && \
    sed -i 's/\r$//' /startapp.sh && \
    chmod +x /usr/local/bin/*.py /startapp.sh

# Set internal environment variables.
# see: https://download.breitbandmessung.de/bbm/
RUN \
    set-cont-env APP_NAME "Breitbandmessung" && \
    set-cont-env APP_VERSION "3.12.1" && \
    set-cont-env APP_SHA256SUM "b948331a4e8df0fcbdd6fbace588770e62b4c61e7e279c6a0f79ef581de080f1" && \
    set-cont-env CHECK_FOR_UPDATES "true" && \
    set-cont-env DEBIAN_FRONTEND "noninteractive" && \
    set-cont-env LANG "de_DE.UTF-8" &&  \
    set-cont-env GTK_MODULES "gail:atk-bridge" && \
    set-cont-env QT_ACCESSIBILITY "1" && \
    true


# Set public environment variables.
# Timezone can be overwritten via docker environment variable
ENV TZ=Europe/Berlin
# 1180x720 is absolute minimum
ENV DISPLAY_WIDTH="1280"
ENV DISPLAY_HEIGHT="768"
ENV TIME_START="13:00"
ENV TIME_END="23:00"


VOLUME /config/xdg/config/Breitbandmessung
