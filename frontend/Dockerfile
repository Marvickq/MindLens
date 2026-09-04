FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 10000

CMD ["sh", "-c", "npm start -- -H 0.0.0.0 -p ${PORT:-10000}"]
