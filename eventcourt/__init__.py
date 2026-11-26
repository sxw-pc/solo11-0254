from . import incident,duty,delivery
MODULES={'incident':incident,'duty':duty,'delivery':delivery}

from . import remedy, resume
MODULES.update(remedy=remedy, resume=resume)
