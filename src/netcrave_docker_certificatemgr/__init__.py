import asyncio
import logging
from netcrave_docker_certificatemgr.http import certificate_manager_service
from netcrave_docker_util.log import configure_logger_for_module


module_logger, main_logger, console_handler = configure_logger_for_module(__name__)

async def start_all():    
    async with asyncio.TaskGroup() as tg:
        await asyncio.gather(tg.create_task(svc.http_listener(cls=certificate_manager_service, 
                                                              bind_host="0.0.0.0", 
                                                              port=80)),
            tg.create_task(svc.https_listener(cls=certificate_manager_service, 
                                              bind_host="0.0.0.0", 
                                              port=443, 
                                              cert_path="/etc/ssl/server.pem", 
                                              key_path="/etc/ssl/server.key", 
                                              ca_cert_path="/etc/ssl/ca.pem")))
        
def daemon():
    try:
        asyncio.get_event_loop().run_until_complete(start_all())
    except asyncio.CancelledError:
        logging.getLogger(__name__).info("Tasks aborted, exiting")
        sys.exit(1)
