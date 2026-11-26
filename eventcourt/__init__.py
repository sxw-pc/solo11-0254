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

from . import slo, advisory
MODULES.update(slo=slo, advisory=advisory)

from . import signal_panel, panel_reader
MODULES.update(signal_panel=signal_panel, panel_reader=panel_reader)

from . import dye_vat, dye_gauge
MODULES.update(dye_vat=dye_vat, dye_gauge=dye_gauge)

from . import checkpress, checkreader
MODULES.update(checkpress=checkpress, checkreader=checkreader)
