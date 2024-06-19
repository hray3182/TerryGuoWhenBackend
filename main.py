import tornado.ioloop
import tornado.web
import tornado.websocket

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message("You said: " + message)

    def on_close(self):
        print("WebSocket closed")

app = tornado.web.Application([
    (r"/", MainHandler),
    (r"/ws", WebSocketHandler),
])

if __name__ == "__main__":
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()