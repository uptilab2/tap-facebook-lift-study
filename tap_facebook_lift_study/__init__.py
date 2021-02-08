#!/usr/bin/env python3
# flake8: noqa
import json
import os

from facebook_business import FacebookSession, FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adaccountuser import AdAccountUser
from facebook_business.apiconfig import ads_api_config
from facebook_business.exceptions import FacebookRequestError
import singer
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema


REQUIRED_CONFIG_KEYS = [
    "client_id",
    "client_secret",
    "token",
    "account_id",
]
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                replication_method="FULL_TABLE",
                key_properties=[],
                metadata=[],
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
            )
        )
    return Catalog(streams)


def sync(config, state, catalog):
    """ Sync data from tap source """
    session = FacebookSession(config['client_id'], config['client_secret'], config['token'])
    client = FacebookAdsApi(session)
    ad_account = AdAccount(config['account_id'], api=client).api_get()

    breakdowns = config['breakdowns'].split(',') if config['breakdowns'] else []

    studies = ad_account.get_ad_studies(['id', 'type', 'name', 'description', 'start_time', 'end_time'])

    # Loop over selected streams in catalog
    for stream in catalog.streams:
        if not stream.schema.selected:
            continue

        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=[],
        )

        if stream.tap_stream_id == 'lift':
            tap_data = get_lift_results(client, studies, breakdowns)
        else:
            raise Exception(f'Stream not yet implemented: {stream.tap_stream_id}')

        singer.write_records(stream.tap_stream_id, tap_data)


def get_lift_results(client, studies, breakdowns):
    # Load cells to add metadata to results
    for study in studies:
        if study.get('type') != 'LIFT':
            continue

        study_data = {
            'study_id': study.get('id'),
            'study_name': study.get('name'),
            'study_description': study.get('description'),
            'study_start_time': study.get('start_time'),
            'study_end_time': study.get('end_time'),
        }

        for objective in study.get_objectives(['id', 'name', 'type', 'is_primary']):
            objective.api_get(
                ['results', 'last_updated_results'],
                params={
                    # ['age', 'gender', 'cell_id', 'country']
                    'breakdowns': breakdowns,
                }
            )

            if not objective.get('results'):
                LOGGER.info(f'Study {study.get("id")} ({stydy.get("name")}) has no results: skipping')
                continue

            objective_data = {
                'objective_id': objective.get('id'),
                'objective_name': objective.get('name'),
                'objective_type': objective.get('type'),
                'objective_is_primary': objective.get('is_primary'),
                'objective_last_updated_results': objective.get('last_updated_results'),
            }

            for result in objective.get('results'):
                result = json.loads(result)
                result_data = {
                    'result_population_test': result.get('population.test', None),
                    'result_population_control': result.get('population.control', None),
                    'result_population_reached': result.get('population.reached', None),
                    'result_impressions': result.get('impressions', None),
                    'result_spend': result.get('spend', None),
                    'result_frequency': result.get('frequency', None),
                    'result_buyers_test': result.get('buyers.test', None),
                    'result_buyers_control': result.get('buyers.control', None),
                    'result_buyers_scaled': result.get('buyers.scaled', None),
                    'result_buyers_incremental': result.get('buyers.incremental', None),
                    'result_buyers_reached': result.get('buyers.reached', None),
                    'result_buyers_reachedPercent': result.get('buyers.reachedPercent', None),
                    'result_buyers_baseline': result.get('buyers.baseline', None),
                    'result_buyers_lift': result.get('buyers.lift', None),
                    'result_buyers_delta': result.get('buyers.delta', None),
                    'result_buyers_pValue': result.get('buyers.pValue', None),
                    'result_buyers_isStatSig': result.get('buyers.isStatSig', None),
                    'result_conversions_test': result.get('conversions.test', None),
                    'result_conversions_control': result.get('conversions.control', None),
                    'result_conversions_scaled': result.get('conversions.scaled', None),
                    'result_conversions_incremental': result.get('conversions.incremental', None),
                    'result_conversions_reached': result.get('conversions.reached', None),
                    'result_conversions_reachedPercent': result.get('conversions.reachedPercent', None),
                    'result_conversions_baseline': result.get('conversions.baseline', None),
                    'result_conversions_lift': result.get('conversions.lift', None),
                    'result_conversions_delta': result.get('conversions.delta', None),
                    'result_conversions_pValue': result.get('conversions.pValue', None),
                    'result_conversions_isStatSig': result.get('conversions.isStatSig', None),
                    'result_advancedConversions_test': result.get('advancedConversions.test', None),
                    'result_advancedConversions_control': result.get('advancedConversions.control', None),
                    'result_advancedConversions_scaled': result.get('advancedConversions.scaled', None),
                    'result_advancedConversions_incremental': result.get('advancedConversions.incremental', None),
                    'result_advancedConversions_baseline': result.get('advancedConversions.baseline', None),
                    'result_advancedConversions_lift': result.get('advancedConversions.lift', None),
                    'result_advancedConversions_informativeSingleCellBayesianConfidence': result.get('advancedConversions.informativeSingleCellBayesianConfidence', None),
                    'result_advancedConversions_informativeMultiCellBayesianConfidence': result.get('advancedConversions.informativeMultiCellBayesianConfidence', None),
                    'result_advancedConversions_bayesianCILower': result.get('advancedConversions.bayesianCILower', None),
                    'result_advancedConversions_bayesianCIUpper': result.get('advancedConversions.bayesianCIUpper', None),
                    'result_age': result.get('age', None),
                    'result_gender': result.get('gender', None),
                    'result_cell_id': result.get('cell_id', None),
                    'result_country': result.get('country', None),
                }

                yield {**study_data, **objective_data, **result_data}


@singer.utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if not args.catalog:
            raise Exception('missing catalog')
        sync(args.config, args.state, args.catalog)


if __name__ == "__main__":
    main()
