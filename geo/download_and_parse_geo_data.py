from os import getcwd

import GEOparse
from pandas import concat


def download_and_parse_geo_data(geo_id, directory_path=getcwd()):

    print('Downloading GEO data into {} ...'.format(directory_path))

    gse = GEOparse.get_GEO(geo=geo_id, destdir=directory_path)

    print('Title: {}'.format(gse.get_metadata_attribute('title')))

    print('N samples: {}'.format(len(gse.get_metadata_attribute('sample_id'))))

    geo_dict = {
        'id_x_sample': None,
        'id_gene_symbol': None,
        'gene_x_sample': None,
        'information_x_sample': None
    }

    values = []

    for sample_id, gsm in gse.gsms.items():

        print('{} ...'.format(sample_id))

        sample_table = gsm.table

        sample_table.columns = sample_table.columns.str.lower().str.replace(
            ' ', '_')

        sample_values = sample_table.set_index('id_ref').squeeze()

        sample_values.name = sample_id

        values.append(sample_values)

    geo_dict['id_x_sample'] = concat(
        values, axis=1).sort_index().sort_index(axis=1)

    print('id_x_sample.shape: {}'.format(geo_dict['id_x_sample'].shape))

    id_gene_symbol = None

    for platform_id, gpl in gse.gpls.items():

        print('{} ...'.format(platform_id))

        platform_table = gpl.table

        platform_table.columns = platform_table.columns.str.lower(
        ).str.replace(' ', '_')

        platform_table.set_index('id', inplace=True)

        if 'gene_symbol' not in platform_table.columns:

            if 'gene_assignment' in platform_table.columns:

                gene_symbols = []

                for assignment in platform_table['gene_assignment']:

                    try:

                        gene_symbols.append(assignment.split('//')[1].strip())

                    except IndexError as exception:

                        print('{}: {}'.format(exception, assignment))

                        gene_symbols.append('NO GENE NAME')

                platform_table['gene_symbol'] = gene_symbols

            elif 'oligoset_genesymbol' in platform_table.columns:

                platform_table['gene_symbol'] = platform_table[
                    'oligoset_genesymbol']

        if 'gene_symbol' in platform_table:

            id_gene_symbol = platform_table['gene_symbol'].dropna()

            print('id_gene_symbol:\n{}'.format(id_gene_symbol))

            geo_dict['id_gene_symbol'] = id_gene_symbol.to_dict()

            gene_x_sample = geo_dict['id_x_sample'].copy()

            id_gene_symbol = geo_dict['id_gene_symbol']

            gene_x_sample.index = geo_dict['id_x_sample'].index.map(
                lambda index: id_gene_symbol.get(str(index), 'NO GENE NAME'))

            gene_x_sample.drop('NO GENE NAME', inplace=True, errors='ignore')

            gene_x_sample.index.name = 'gene_symbol'

            geo_dict['gene_x_sample'] = gene_x_sample.sort_index().sort_index(
                axis=1)

            print('gene_x_sample.shape: {}'.format(geo_dict['gene_x_sample']
                                                   .shape))

        else:

            print(
                '\tgene_symbol is not a GPL column ({}); IDs may be already gene symbols.'.
                format(', '.join(platform_table.columns)))

        geo_dict['information_x_sample'] = gse.phenotype_data.T

        print('information:\n\t{}'.format('\n\t'.join(
            geo_dict['information_x_sample'].index)))

    return geo_dict
