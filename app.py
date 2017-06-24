from aiohttp import web
import handler
import room

app = web.Application()
# dict from scene name to ws
app['Players'] = list()

# register of the room
app['Rooms'] = list()
for i in range(4):
    app['Rooms'].append(room.Room(i))

app.router.add_get('/ws', handler.handler)
web.run_app(app)


