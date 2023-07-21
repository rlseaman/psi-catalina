import argparse


class Opts:
    def __init__(self, args:argparse.Namespace):
        self.validation_opts = ValidationOpts(args)
        self.preprocessing_opts = PreprocessingOpts(args)
        self.postprocessing_opts = PostprocessingOpts(args)
        self.filter_opts = FilterOpts(args)
        self.location_opts = LocationOpts(args)
        self.console = args.console
        self.verbose = args.verbose


class ValidationOpts:
    def __init__(self, args:argparse.Namespace):
       self.skip_validation=args.skip_validation
       self.skip_data_validation=args.skip_data_validation
       self.permissive_validation=args.permissive_validation


class PreprocessingOpts:
    def __init__(self, args:argparse.Namespace):
        self.skip_preprocessing=args.skip_preprocessing
        self.skip_data_preprocessing=args.skip_data_preprocessing
        self.skip_label_preprocessing=args.skip_label_preprocessing


class PostprocessingOpts:
    def __init__(self, args:argparse.Namespace):
        self.skip_move=args.skip_move
        self.dry_move=args.dry_move
        self.copy_files=args.copy_files
        self.skip_collection_update=args.skip_collection_update
        self.preserve_collection_version=args.preserve_collection_version
        self.validate_only=args.validate_only


class FilterOpts:
    def __init__(self, args:argparse.Namespace):
        self.specific_date = args.specific_date
        self.specific_instrument = args.specific_instrument
        self.max_products = args.max_products
        self.max_nights = args.max_nights
        self.ignore_past_days = args.ignore_past_days


class LocationOpts:
    def __init__(self, args:argparse.Namespace):
        self.basedir=args.basedir
        self.destdir=args.destdir
        self.validated_dir=args.validated_dir
        self.failure_dir=args.failed_dir
        self.schemadir=args.schemadir


def get_args() -> Opts:
    parser = argparse.ArgumentParser(description='Validate a PDS4 collection inventory against the directory')
    parser.add_argument('--basedir', 
                        help='The base directory for the delivered data', 
                        required=True)
    parser.add_argument('--destdir', 
                        help='The destination directory for the processed data', 
                        required=True)
    parser.add_argument('--validated-dir', 
                        help='The destination directory for validated data (overrides destdir)', 
                        required=False)
    parser.add_argument('--failed-dir', 
                        help='The destination directory for failed data (overrides destdir)', 
                        required=False)
    parser.add_argument('--schemadir', 
                        help='The directory for the schema files', 
                        required=True)
    parser.add_argument('--specific-date', 
                        dest='specific_date', 
                        help='If provided, will only process the specified date')
    parser.add_argument('--specific-instrument', 
                        dest='specific_instrument', 
                        help='If provided, will only process the specified instrument')
    parser.add_argument('--skip-preprocessing', 
                        action='store_true', dest='skip_preprocessing', 
                        help='If enabled, will not preprocess the data and label files')
    parser.add_argument('--skip-data-preprocessing', 
                        action='store_true', dest='skip_data_preprocessing', 
                        help='If enabled, will not preprocess the data files')
    parser.add_argument('--skip-label-preprocessing', 
                        action='store_true', 
                        dest='skip_label_preprocessing', 
                        help='If enabled, will not preprocess the label files')
    parser.add_argument('--skip-validation', 
                        action='store_true', 
                        dest='skip_validation', 
                        help='If enabled, will not validate the data')
    parser.add_argument('--permissive-validation', 
                        action='store_true', dest='permissive_validation', 
                        help='If enabled, will continue even if there are validation errors')
    parser.add_argument('--skip-data-validation', 
                        action='store_true', 
                        dest='skip_data_validation', 
                        help='If enabled, will not validate the data')
    parser.add_argument('--skip-move', 
                        action='store_true', 
                        dest='skip_move', 
                        help='If enabled, will not move the data')
    parser.add_argument('--dry-move', 
                        action='store_true', 
                        dest='dry_move', 
                        help='If enabled, will not move the data, but will log the calculated destination')
    parser.add_argument('--copy-files', 
                        action='store_true', 
                        dest='copy_files', 
                        help='If enabled, will not move the data, but will copy it instead')
    parser.add_argument('--skip-collection-update', 
                        action='store_true', 
                        dest='skip_collection_update', 
                        help='If enabled, will not update the collection inventory or label')
    parser.add_argument('--preserve-collection-version', 
                        action='store_true', 
                        dest='preserve_collection_version', 
                        help='If enabled, will not update the collection version numbers')
    parser.add_argument('--console', 
                        action='store_true', 
                        dest='console', 
                        help='If enabled, will log to console instead of log file')
    parser.add_argument('--verbose', 
                        action='store_true', 
                        dest='verbose', 
                        help='If enabled, will add more info to logs')
    parser.add_argument('--max-products', 
                        type=int,
                        dest='max_products', 
                        help='The maximum number of products to process in a single run')
    parser.add_argument('--max-nights', 
                        type=int,
                        dest='max_nights', 
                        help='The maximum number of nights to process in a single run')
    parser.add_argument('--ignore-past-days', 
                        type=int,
                        default=0,
                        dest='ignore_past_days', 
                        help='Ignores products dated in the past x number of days. This will give products time to accumulate before processing')
    parser.add_argument('--validate-only', 
                        action='store_true', 
                        dest='validate_only', 
                        help='Only perform validation. Passing products will be moved to the destination directory, but they will not be organized in collections.')

    return Opts(parser.parse_args())
