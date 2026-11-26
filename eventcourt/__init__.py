from . import incident,duty,delivery
MODULES={'incident':incident,'duty':duty,'delivery':delivery}

from . import remedy, resume
MODULES.update(remedy=remedy, resume=resume)

from . import channel, cost, bulletin
MODULES.update(channel=channel, cost=cost, bulletin=bulletin)
