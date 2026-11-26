from . import incident,duty,delivery
MODULES={'incident':incident,'duty':duty,'delivery':delivery}

from . import remedy, resume
MODULES.update(remedy=remedy, resume=resume)

from . import channel, cost, bulletin
MODULES.update(channel=channel, cost=cost, bulletin=bulletin)

from . import muster, timeline
MODULES.update(muster=muster, timeline=timeline)

from . import watch, notice_cost
MODULES.update(watch=watch, notice_cost=notice_cost)

from . import airgap, witness
MODULES.update(airgap=airgap,witness=witness)
