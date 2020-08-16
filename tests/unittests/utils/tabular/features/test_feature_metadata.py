import pytest

from autogluon.utils.tabular.features.feature_metadata import FeatureMetadata


def test_feature_metadata(data_helper):
    # Given
    input_data = data_helper.generate_multi_feature_full()

    expected_feature_metadata_full = {
        ('category', ()): ['cat'],
        ('datetime', ()): ['datetime'],
        ('float', ()): ['float'],
        ('int', ()): ['int'],
        ('object', ()): ['obj'],
        ('object', ('datetime_as_object',)): ['datetime_as_object'],
        ('object', ('text',)): ['text']
    }

    expected_feature_metadata_get_features = ['int', 'float', 'obj', 'cat', 'datetime', 'text', 'datetime_as_object']

    expected_type_map_raw = {
        'cat': 'category',
        'datetime': 'datetime',
        'datetime_as_object': 'object',
        'float': 'float',
        'int': 'int',
        'obj': 'object',
        'text': 'object'
    }

    expected_type_group_map_special = {
        'datetime_as_object': ['datetime_as_object'],
        'text': ['text']
    }

    expected_feature_metadata_renamed_full = {
        ('category', ()): ['cat'],
        ('datetime', ()): ['datetime'],
        ('float', ()): ['obj'],
        ('int', ()): ['int_renamed'],
        ('object', ()): ['float'],
        ('object', ('datetime_as_object',)): ['datetime_as_object'],
        ('object', ('text',)): ['text_renamed']
    }

    expected_feature_metadata_recombined_full_full = {
        ('category', ()): ['cat'],
        ('custom_raw_type', ('custom_special_type',)): ['new_feature'],
        ('datetime', ()): ['datetime'],
        ('float', ()): ['float'],
        ('int', ('custom_special_type',)): ['int'],
        ('object', ()): ['obj'],
        ('object', ('datetime_as_object',)): ['datetime_as_object'],
        ('object', ('text',)): ['text']
    }

    # When
    feature_metadata = FeatureMetadata.from_df(input_data)
    feature_metadata_renamed = feature_metadata.rename_features(rename_map={'text': 'text_renamed', 'int': 'int_renamed', 'obj': 'float', 'float': 'obj'})
    feature_metadata_remove = feature_metadata.remove_features(features=['text', 'obj', 'float'])
    feature_metadata_keep = feature_metadata.keep_features(features=['text', 'obj', 'float'])
    feature_metadata_custom = FeatureMetadata(
        type_map_raw={'int': 'int', 'new_feature': 'custom_raw_type'},
        type_group_map_special={'custom_special_type': ['int', 'new_feature']}
    )
    feature_metadata_recombined = feature_metadata_keep.join_metadata(feature_metadata_remove)
    feature_metadata_recombined_alternate = FeatureMetadata.join_metadatas(metadata_list=[feature_metadata_keep, feature_metadata_remove])
    feature_metadata_recombined_full = FeatureMetadata.join_metadatas(metadata_list=[feature_metadata_keep, feature_metadata_remove, feature_metadata_custom], shared_raw_features='error_if_diff')

    # Therefore
    with pytest.raises(AssertionError):
        # Error because special contains feature not in raw
        FeatureMetadata(
            type_map_raw={'int': 'int'},
            type_group_map_special={'custom_special_type': ['int', 'new_feature']}
        )
    with pytest.raises(AssertionError):
        # Error because renaming to another existing feature without also renaming that feature
        feature_metadata.rename_features(rename_map={'text': 'obj'})
    with pytest.raises(KeyError):
        # Error if removing unknown feature
        feature_metadata_remove.remove_features(features=['text'])
    with pytest.raises(KeyError):
        # Error if getting unknown feature type
        feature_metadata_remove.get_feature_type_raw('text')
    with pytest.raises(KeyError):
        # Error if getting unknown feature type
        feature_metadata_remove.get_feature_types_special('text')
    with pytest.raises(AssertionError):
        # Error because feature_metadata_remove and feature_metadata_custom share a raw feature
        FeatureMetadata.join_metadatas(metadata_list=[feature_metadata_keep, feature_metadata_remove, feature_metadata_custom])

    assert feature_metadata.get_feature_metadata_full() == expected_feature_metadata_full
    assert feature_metadata.get_features() == expected_feature_metadata_get_features
    assert feature_metadata.type_map_raw == expected_type_map_raw
    assert dict(feature_metadata.type_group_map_special) == expected_type_group_map_special

    assert feature_metadata.get_feature_type_raw('text') == 'object'
    assert feature_metadata.get_feature_types_special('text') == ['text']
    assert feature_metadata.get_feature_type_raw('int') == 'int'
    assert feature_metadata.get_feature_types_special('int') == []
    assert feature_metadata_recombined_full.get_feature_types_special('int') == ['custom_special_type']
    assert feature_metadata_recombined_full.get_feature_type_raw('new_feature') == 'custom_raw_type'

    assert feature_metadata_renamed.get_feature_metadata_full() == expected_feature_metadata_renamed_full
    assert feature_metadata_recombined.get_feature_metadata_full() == feature_metadata.get_feature_metadata_full()
    assert feature_metadata_recombined_alternate.get_feature_metadata_full() == feature_metadata.get_feature_metadata_full()
    assert feature_metadata_recombined_full.get_feature_metadata_full() == expected_feature_metadata_recombined_full_full