'''
@author MManning
@file ion/processes/data/transforms/ctd/ctd_L1_conductivity.py
@description Transforms CTD parsed data into L1 product for conductivity
'''

from pyon.ion.transform import TransformFunction
from pyon.service.service import BaseService
from pyon.core.exception import BadRequest
from pyon.public import IonObject, RT, log
from decimal import *

#from interface.services.dm.ipubsub_management_service import PubsubManagementServiceClient

from prototype.sci_data.ctd_stream import scalar_point_stream_definition, ctd_stream_definition

from prototype.sci_data.deconstructor_apis import PointSupplementDeconstructor
from prototype.sci_data.constructor_apis import PointSupplementConstructor

from seawater.gibbs import SP_from_cndr
from seawater.gibbs import cte

class CTDL1ConductivityTransform(TransformFunction):
    ''' A basic transform that receives input through a subscription,
    parses the input from a CTD, extracts the conductivity value and scales it according to
    the defined algorithm. If the transform
    has an output_stream it will publish the output on the output stream.

    '''


    # Make the stream definitions of the transform class attributes... best available option I can think of?
    outgoing_stream_def = scalar_point_stream_definition(
        description='L1 Conductivity Scale data from science transform',
        field_name = 'L1_conductivity',
        field_definition = 'http://http://sweet.jpl.nasa.gov/2.2/quanConductivity.owl#Conductivity',
        field_units_code = '', # http://unitsofmeasure.org/ticket/27 Has no Units!
        field_range = [0.1, 40.0]
    )

    incoming_stream_def = ctd_stream_definition()




    def execute(self, granule):
        """Processes incoming data!!!!
        """

        # Use the deconstructor to pull data from a granule
        psd = PointSupplementDeconstructor(stream_definition=self.incoming_stream_def, stream_granule=granule)


        conductivity = psd.get_values('conductivity')
        pressure = psd.get_values('pressure')
        temperature = psd.get_values('temperature')

        longitude = psd.get_values('longitude')
        latitude = psd.get_values('latitude')
        time = psd.get_values('time')

        log.warn('Got conductivity: %s' % str(conductivity))


        # The L1 conductivity data product algorithm takes the L0 conductivity data product and converts it
        # into Siemens per meter (S/m)
        #    SBE 37IM Output Format 0
        #    1) Standard conversion from 5-character hex string (Chex) to decimal (Cdec)
        #    2) Scaling: C [S/m] = (Cdec / 100,000) – 0.5

        # Use the constructor to put data into a granule
        psc = PointSupplementConstructor(point_definition=self.outgoing_stream_def)

        for i in xrange(len(conductivity)):
            scaled_conductivity =  ( Decimal(conductivity[i]) / 100000 ) - 0.5
            point_id = psc.add_point(time=time[i],location=(longitude[i],latitude[i],pressure[i]))
            psc.add_scalar_point_coverage(point_id=point_id, coverage_id='conductivity', value=scaled_conductivity)

        return psc.close_stream_granule()

  