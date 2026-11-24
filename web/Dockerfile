# The web as a container: the static build served by an unprivileged nginx.
#
# The Supabase variables are baked at build time, because Vite inlines them:
#   docker build -t anden9-web \
#     --build-arg VITE_SUPABASE_URL=https://project.supabase.co \
#     --build-arg VITE_SUPABASE_ANON_KEY=... web
#
# It listens on 3000, which is the container port most platforms ask for, and honours a PORT
# variable when the platform injects its own.
FROM node:24-alpine AS build

WORKDIR /app

RUN corepack enable

# Dependencies first, so a source change does not reinstall them.
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# Vite reads these at build time and inlines them into the bundle. An empty value
# is allowed: the app then renders the shell and says "sin datos".
ARG VITE_SUPABASE_URL=""
ARG VITE_SUPABASE_ANON_KEY=""
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL} \
    VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}
RUN pnpm build

FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime

# The image already runs as uid 101 and listens on PORT, no root anywhere.
# The entrypoint of this image runs envsubst over /etc/nginx/templates, so a platform that
# injects PORT gets it without touching the config.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

ENV PORT=3000
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --output-document=- http://127.0.0.1:${PORT}/healthz || exit 1
