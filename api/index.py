from mangum import Mangum
from judgement_portal.asgi import application

handler = Mangum(application)
