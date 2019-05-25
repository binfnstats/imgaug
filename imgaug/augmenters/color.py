"""
Augmenters that apply color space oriented changes.

Do not import directly from this file, as the categorization is not final.
Use instead ::

    from imgaug import augmenters as iaa

and then e.g. ::

    seq = iaa.Sequential([
        iaa.Grayscale((0.0, 1.0)),
        iaa.AddToHueAndSaturation((-10, 10))
    ])

List of augmenters:

    * InColorspace (deprecated)
    * WithColorspace
    * AddToHueAndSaturation
    * ChangeColorspace
    * Grayscale

"""
from __future__ import print_function, division, absolute_import

import numpy as np
import cv2
import six.moves as sm

from . import meta
from . import blend
import imgaug as ia
from .. import parameters as iap
from .. import dtypes as iadt


@ia.deprecated(alt_func="WithColorspace")
def InColorspace(to_colorspace, from_colorspace="RGB", children=None, name=None, deterministic=False,
                 random_state=None):
    """Convert images to another colorspace."""
    return WithColorspace(to_colorspace, from_colorspace, children, name, deterministic, random_state)


class WithColorspace(meta.Augmenter):
    """
    Apply child augmenters within a specific colorspace.

    This augumenter takes a source colorspace A and a target colorspace B
    as well as children C. It changes images from A to B, then applies the
    child augmenters C and finally changes the colorspace back from B to A.
    See also ChangeColorspace() for more.

    dtype support::

        * ``uint8``: yes; fully tested
        * ``uint16``: ?
        * ``uint32``: ?
        * ``uint64``: ?
        * ``int8``: ?
        * ``int16``: ?
        * ``int32``: ?
        * ``int64``: ?
        * ``float16``: ?
        * ``float32``: ?
        * ``float64``: ?
        * ``float128``: ?
        * ``bool``: ?

    Parameters
    ----------
    to_colorspace : str
        See :func:`imgaug.augmenters.ChangeColorspace.__init__`.

    from_colorspace : str, optional
        See :func:`imgaug.augmenters.ChangeColorspace.__init__`.

    children : None or Augmenter or list of Augmenters, optional
        See :func:`imgaug.augmenters.ChangeColorspace.__init__`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> aug = iaa.WithColorspace(to_colorspace="HSV", from_colorspace="RGB",
    >>>                          children=iaa.WithChannels(0, iaa.Add(10)))

    This augmenter will add 10 to Hue value in HSV colorspace,
    then change the colorspace back to the original (RGB).

    """

    def __init__(self, to_colorspace, from_colorspace="RGB", children=None, name=None, deterministic=False,
                 random_state=None):
        super(WithColorspace, self).__init__(name=name, deterministic=deterministic, random_state=random_state)

        self.to_colorspace = to_colorspace
        self.from_colorspace = from_colorspace
        self.children = meta.handle_children_list(children, self.name, "then")

    def _augment_images(self, images, random_state, parents, hooks):
        result = images
        if hooks is None or hooks.is_propagating(images, augmenter=self, parents=parents, default=True):
            result = ChangeColorspace(
                to_colorspace=self.to_colorspace,
                from_colorspace=self.from_colorspace
            ).augment_images(images=result)
            result = self.children.augment_images(
                images=result,
                parents=parents + [self],
                hooks=hooks
            )
            result = ChangeColorspace(
                to_colorspace=self.from_colorspace,
                from_colorspace=self.to_colorspace
            ).augment_images(images=result)
        return result

    def _augment_heatmaps(self, heatmaps, random_state, parents, hooks):
        result = heatmaps
        if hooks is None or hooks.is_propagating(heatmaps, augmenter=self, parents=parents, default=True):
            result = self.children.augment_heatmaps(
                result,
                parents=parents + [self],
                hooks=hooks,
            )
        return result

    def _augment_keypoints(self, keypoints_on_images, random_state, parents, hooks):
        result = keypoints_on_images
        if hooks is None or hooks.is_propagating(keypoints_on_images, augmenter=self, parents=parents, default=True):
            result = self.children.augment_keypoints(
                result,
                parents=parents + [self],
                hooks=hooks,
            )
        return result

    def _to_deterministic(self):
        aug = self.copy()
        aug.children = aug.children.to_deterministic()
        aug.deterministic = True
        aug.random_state = ia.derive_random_state(self.random_state)
        return aug

    def get_parameters(self):
        return [self.channels]

    def get_children_lists(self):
        return [self.children]

    def __str__(self):
        return "WithColorspace(from_colorspace=%s, to_colorspace=%s, name=%s, children=[%s], deterministic=%s)" % (
            self.from_colorspace, self.to_colorspace, self.name, self.children, self.deterministic)


# TODO removed deterministic and random_state here as parameters, because this
# function creates multiple child augmenters. not sure if this is sensible
# (give them all the same random state instead?)
# TODO this is for now deactivated, because HSV images returned by opencv have value range 0-180 for the hue channel
# and are supposed to be angular representations, i.e. if values go below 0 or above 180 they are supposed to overflow
# to 180 and 0
"""
def AddToHueAndSaturation(value=0, per_channel=False, from_colorspace="RGB", channels=[0, 1], name=None):  # pylint: disable=locally-disabled, dangerous-default-value, line-too-long
    ""
    Augmenter that transforms images into HSV space, selects the H and S
    channels and then adds a given range of values to these.

    Parameters
    ----------
    value : int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        See :func:`imgaug.augmenters.arithmetic.Add.__init__()`.

    per_channel : bool or float, optional
        See :func:`imgaug.augmenters.arithmetic.Add.__init__()`.

    from_colorspace : str, optional
        See :func:`imgaug.augmenters.color.ChangeColorspace.__init__()`.

    channels : int or list of int or None, optional
        See :func:`imgaug.augmenters.meta.WithChannels.__init__()`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> aug = AddToHueAndSaturation((-20, 20), per_channel=True)

    Adds random values between -20 and 20 to the hue and saturation
    (independently per channel and the same value for all pixels within
    that channel).

    ""
    if name is None:
        name = "Unnamed%s" % (ia.caller_name(),)

    return WithColorspace(
        to_colorspace="HSV",
        from_colorspace=from_colorspace,
        children=meta.WithChannels(
            channels=channels,
            children=arithmetic.Add(value=value, per_channel=per_channel)
        ),
        name=name
    )
"""


class AddToHueAndSaturation(meta.Augmenter):
    """
    Augmenter that increases/decreases hue and saturation by random values.

    The augmenter first transforms images to HSV colorspace, then adds random values to the H and S channels
    and afterwards converts back to RGB.

    TODO add float support

    dtype support::

        * ``uint8``: yes; fully tested
        * ``uint16``: no
        * ``uint32``: no
        * ``uint64``: no
        * ``int8``: no
        * ``int16``: no
        * ``int32``: no
        * ``int64``: no
        * ``float16``: no
        * ``float32``: no
        * ``float64``: no
        * ``float128``: no
        * ``bool``: no

    Parameters
    ----------
    value : None or int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        Value to add to the hue *and* saturation of all pixels.
        It is expected to be in the range ``-255`` to ``+255``.

            * If this is ``None``, `value_hue` and/or `value_saturation`
              may be set to values other than ``None``.
            * If an integer, then that value will be used for all images.
            * If a tuple ``(a, b)``, then a value from the discrete
              range ``[a, b]`` will be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, then a value will be sampled from that
              parameter per image.

    value_hue : None or int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        Value to add to the hue of all pixels.
        This is expected to be in the range ``-255`` to ``+255`` and will
        automatically be projected to an angular representation using
        ``(hue/255) * (360/2)`` (OpenCV's hue representation is in the
        range ``[0, 180]`` instead of ``[0, 360]``).
        Only this or `value` may be set, not both.

            * If this and `value_saturation` are both ``None``, `value` may
              be set to a non-``None`` value.
            * If an integer, then that value will be used for all images.
            * If a tuple ``(a, b)``, then a value from the discrete
              range ``[a, b]`` will be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, then a value will be sampled from that
              parameter per image.

    value_saturation : None or int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        Value to add to the saturation of all pixels.
        It is expected to be in the range ``-255`` to ``+255``.
        Only this or `value` may be set, not both.

            * If this and `value_hue` are both ``None``, `value` may
              be set to a non-``None`` value.
            * If an integer, then that value will be used for all images.
            * If a tuple ``(a, b)``, then a value from the discrete
              range ``[a, b]`` will be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, then a value will be sampled from that
              parameter per image.

    per_channel : bool or float, optional
        Whether to sample per image only one value from `value` and use it for
        both hue and saturation (``False``) or to sample independently one
        value for hue and one for saturation (``True``).
        If this value is a float ``p``, then for ``p`` percent of all images
        `per_channel` will be treated as ``True``, otherwise as ``False``.

        This parameter has no effect is `value_hue` and/or `value_saturation`
        are used instead of `value`.

    from_colorspace : str, optional
        See :func:`imgaug.augmenters.color.ChangeColorspace.__init__()`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> import imgaug.augmenters as iaa
    >>> aug = iaa.AddToHueAndSaturation((-20, 20), per_channel=True)

    Adds random values between -20 and 20 to the hue and saturation
    (independently per channel and the same value for all pixels within
    that channel). The hue will be automatically projected to an angular
    representation.

    """

    _LUT_CACHE = None

    def __init__(self, value=None, value_hue=None, value_saturation=None,
                 per_channel=False, from_colorspace="RGB",
                 name=None, deterministic=False, random_state=None):
        super(AddToHueAndSaturation, self).__init__(
            name=name, deterministic=deterministic, random_state=random_state)

        self.value = self._handle_value_arg(value, value_hue, value_saturation)
        self.value_hue = self._handle_value_hue_arg(value_hue)
        self.value_saturation = self._handle_value_saturation_arg(
            value_saturation)
        self.per_channel = iap.handle_probability_param(per_channel,
                                                        "per_channel")

        # we don't change these in a modified to_deterministic() here,
        # because they are called in _augment_images() with random states
        self.colorspace_changer = ChangeColorspace(
            from_colorspace=from_colorspace, to_colorspace="HSV")
        self.colorspace_changer_inv = ChangeColorspace(
            from_colorspace="HSV", to_colorspace=from_colorspace)

        self.backend = "cv2"

        # precompute tables for cv2.LUT
        if self.backend == "cv2" and self._LUT_CACHE is None:
            self._LUT_CACHE = self._generate_lut_table()

    def _draw_samples(self, augmentables, random_state):
        nb_images = len(augmentables)
        rss = ia.derive_random_states(random_state, 2)

        if self.value is not None:
            per_channel = self.per_channel.draw_samples(
                (nb_images,), random_state=rss[0])
            per_channel = (per_channel > 0.5)

            samples = self.value.draw_samples(
                (nb_images, 2), random_state=rss[1]).astype(np.int32)
            assert (-255 <= samples[0, 0] <= 255), (
                "Expected values sampled from `value` in AddToHueAndSaturation "
                "to be in range [-255, 255], but got %.8f." % (samples[0, 0])
            )

            samples_hue = samples[:, 0]
            samples_saturation = np.copy(samples[:, 0])
            samples_saturation[per_channel] = samples[per_channel, 1]
        else:
            if self.value_hue is not None:
                samples_hue = self.value_hue.draw_samples(
                    (nb_images,), random_state=rss[0]).astype(np.int32)
            else:
                samples_hue = np.zeros((nb_images,), dtype=np.int32)

            if self.value_saturation is not None:
                samples_saturation = self.value_saturation.draw_samples(
                    (nb_images,), random_state=rss[1]).astype(np.int32)
            else:
                samples_saturation = np.zeros((nb_images,), dtype=np.int32)

        # project hue to angular representation
        # OpenCV uses range [0, 180] for the hue
        samples_hue = (
            (samples_hue.astype(np.float32) / 255.0) * (360/2)
        ).astype(np.int32)

        return samples_hue, samples_saturation

    def _augment_images(self, images, random_state, parents, hooks):
        input_dtypes = iadt.copy_dtypes_for_restore(images, force_list=True)

        result = images

        # surprisingly, placing this here seems to be slightly slower than
        # placing it inside the loop
        # if isinstance(images_hsv, list):
        #    images_hsv = [img.astype(np.int32) for img in images_hsv]
        # else:
        #    images_hsv = images_hsv.astype(np.int32)

        rss = ia.derive_random_states(random_state, 3)
        images_hsv = self.colorspace_changer._augment_images(
            images, rss[0], parents + [self], hooks)
        samples = self._draw_samples(images, rss[1])
        hues = samples[0]
        saturations = samples[1]
        rs_inv = rss[2]

        # this is needed if no cache for LUT is used:
        # value_range = np.arange(0, 256, dtype=np.int16)

        gen = enumerate(zip(images_hsv, hues, saturations))
        for i, (image_hsv, hue_i, saturation_i) in gen:
            assert image_hsv.dtype.name == "uint8"

            if self.backend == "cv2":
                image_hsv = self._transform_image_cv2(
                    image_hsv, hue_i, saturation_i)
            else:
                image_hsv = self._transform_image_numpy(
                    image_hsv, hue_i, saturation_i)

            image_hsv = image_hsv.astype(input_dtypes[i])
            # the inverse colorspace changer has a deterministic output
            # (always <from_colorspace>, so that can always provide it the
            # same random state as input
            image_rgb = self.colorspace_changer_inv._augment_images(
                [image_hsv], rs_inv, parents + [self], hooks)[0]
            result[i] = image_rgb

        return result

    def _transform_image_cv2(self, image_hsv, hue, saturation):
        # this has roughly the same speed as the numpy backend
        # for 64x64 and is about 25% faster for 224x224

        # code without using cache:
        # table_hue = np.mod(value_range + sample_hue, 180)
        # table_saturation = np.clip(value_range + sample_saturation, 0, 255)

        # table_hue = table_hue.astype(np.uint8, copy=False)
        # table_saturation = table_saturation.astype(np.uint8, copy=False)

        # image_hsv[..., 0] = cv2.LUT(image_hsv[..., 0], table_hue)
        # image_hsv[..., 1] = cv2.LUT(image_hsv[..., 1], table_saturation)

        # code with using cache (at best maybe 10% faster for 64x64):
        image_hsv[..., 0] = cv2.LUT(
            image_hsv[..., 0], self._LUT_CACHE[0][int(hue)])
        image_hsv[..., 1] = cv2.LUT(
            image_hsv[..., 1], self._LUT_CACHE[1][int(saturation)])
        return image_hsv

    @classmethod
    def _transform_image_numpy(cls, image_hsv, hue, saturation):
        # int16 seems to be slightly faster than int32
        image_hsv = image_hsv.astype(np.int16)
        # np.mod() works also as required here for negative values
        image_hsv[..., 0] = np.mod(image_hsv[..., 0] + hue, 180)
        image_hsv[..., 1] = np.clip(
            image_hsv[..., 1] + saturation, 0, 255)
        return image_hsv

    def _augment_heatmaps(self, heatmaps, random_state, parents, hooks):
        return heatmaps

    def _augment_keypoints(self, keypoints_on_images, random_state, parents,
                           hooks):
        return keypoints_on_images

    def get_parameters(self):
        return [self.value, self.value_hue, self.value_saturation,
                self.per_channel]

    @classmethod
    def _handle_value_arg(cls, value, value_hue, value_saturation):
        if value is not None:
            assert value_hue is None, (
                "`value_hue` may not be set if `value` is set. "
                "It is set to: %s (type: %s)." % (
                    str(value_hue), type(value_hue))
            )
            assert value_saturation is None, (
                "`value_saturation` may not be set if `value` is set. "
                "It is set to: %s (type: %s)." % (
                    str(value_saturation), type(value_saturation))
            )
            return iap.handle_discrete_param(
                value, "value", value_range=(-255, 255), tuple_to_uniform=True,
                list_to_choice=True, allow_floats=False)

        return None

    @classmethod
    def _handle_value_hue_arg(cls, value_hue):
        if value_hue is not None:
            # we don't have to verify here the value is None, as the
            # exclusivity was already ensured in _handle_value_arg()
            return iap.handle_discrete_param(
                value_hue, "value_hue", value_range=(-255, 255),
                tuple_to_uniform=True, list_to_choice=True, allow_floats=False)

        return None

    @classmethod
    def _handle_value_saturation_arg(cls, value_saturation):
        if value_saturation is not None:
            # we don't have to verify here the value is None, as the
            # exclusivity was already ensured in _handle_value_arg()
            return iap.handle_discrete_param(
                value_saturation, "value_saturation", value_range=(-255, 255),
                tuple_to_uniform=True, list_to_choice=True, allow_floats=False)
        return None

    @classmethod
    def _generate_lut_table(cls):
        table = (np.zeros((256*2, 256), dtype=np.int8),
                 np.zeros((256*2, 256), dtype=np.int8))
        value_range = np.arange(0, 256, dtype=np.int16)
        # this could be done slightly faster by vectorizing the loop
        for i in sm.xrange(-255, 255+1):
            table_hue = np.mod(value_range + i, 180)
            table_saturation = np.clip(value_range + i, 0, 255)
            table[0][i, :] = table_hue
            table[1][i, :] = table_saturation
        return table


def AddToHue(value, from_colorspace="RGB", name=None, deterministic=False,
             random_state=None):
    """
    Add random values to the hue of images.

    The augmenter first transforms images to HSV colorspace, then adds random
    values to the H channel and afterwards converts back to RGB.

    If you want to change both the hue and the saturation, it is recommended
    to use ``AddToHueAndSaturation`` as otherwise the image will be
    converted twice to HSV and back to RGB.

    dtype support::

        See `imgaug.augmenters.color.AddToHueAndSaturation`.

    Parameters
    ----------
    value : None or int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        Value to add to the hue of all pixels.
        This is expected to be in the range ``-255`` to ``+255`` and will
        automatically be projected to an angular representation using
        ``(hue/255) * (360/2)`` (OpenCV's hue representation is in the
        range ``[0, 180]`` instead of ``[0, 360]``).

            * If an integer, then that value will be used for all images.
            * If a tuple ``(a, b)``, then a value from the discrete
              range ``[a, b]`` will be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, then a value will be sampled from that
              parameter per image.

    from_colorspace : str, optional
        See :func:`imgaug.augmenters.color.ChangeColorspace.__init__()`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> import imgaug.augmenters as iaa
    >>> aug = iaa.AddToHue((-20, 20))

    Samples random values from the discrete uniform range ``[-20..20]``,
    converts them to angular representation and adds them to the hue, i.e.
    to the H channel in HSV colorspace.

    """
    if name is None:
        name = "Unnamed%s" % (ia.caller_name(),)

    return AddToHueAndSaturation(
        value_hue=value,
        from_colorspace=from_colorspace,
        name=name,
        deterministic=deterministic,
        random_state=random_state)


def AddToSaturation(value, from_colorspace="RGB", name=None,
                    deterministic=False, random_state=None):
    """
    Add random values to the saturation of images.

    The augmenter first transforms images to HSV colorspace, then adds random
    values to the S channel and afterwards converts back to RGB.

    If you want to change both the hue and the saturation, it is recommended
    to use ``AddToHueAndSaturation`` as otherwise the image will be
    converted twice to HSV and back to RGB.

    dtype support::

        See `imgaug.augmenters.color.AddToHueAndSaturation`.

    Parameters
    ----------
    value : None or int or tuple of int or list of int or imgaug.parameters.StochasticParameter, optional
        Value to add to the saturation of all pixels.
        It is expected to be in the range ``-255`` to ``+255``.

            * If an integer, then that value will be used for all images.
            * If a tuple ``(a, b)``, then a value from the discrete
              range ``[a, b]`` will be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, then a value will be sampled from that
              parameter per image.

    from_colorspace : str, optional
        See :func:`imgaug.augmenters.color.ChangeColorspace.__init__()`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> import imgaug.augmenters as iaa
    >>> aug = iaa.AddToSaturation((-20, 20))

    Samples random values from the discrete uniform range ``[-20..20]``,
    and adds them to the saturation, i.e. to the S channel in HSV colorspace.

    """
    if name is None:
        name = "Unnamed%s" % (ia.caller_name(),)

    return AddToHueAndSaturation(
        value_saturation=value,
        from_colorspace=from_colorspace,
        name=name,
        deterministic=deterministic,
        random_state=random_state)


# TODO tests
# Note: Not clear whether this class will be kept (for anything aside from grayscale)
# other colorspaces dont really make sense and they also might not work correctly
# due to having no clearly limited range (like 0-255 or 0-1)
# TODO rename to ChangeColorspace3D and then introduce ChangeColorspace, which does not enforce 3d images?
class ChangeColorspace(meta.Augmenter):
    """
    Augmenter to change the colorspace of images.

    NOTE: This augmenter is not tested. Some colorspaces might work, others might not.

    NOTE: This augmenter tries to project the colorspace value range on 0-255. It outputs dtype=uint8 images.

    TODO check dtype support

    dtype support::

        * ``uint8``: yes; not tested
        * ``uint16``: ?
        * ``uint32``: ?
        * ``uint64``: ?
        * ``int8``: ?
        * ``int16``: ?
        * ``int32``: ?
        * ``int64``: ?
        * ``float16``: ?
        * ``float32``: ?
        * ``float64``: ?
        * ``float128``: ?
        * ``bool``: ?

    Parameters
    ----------
    to_colorspace : str or list of str or imgaug.parameters.StochasticParameter
        The target colorspace.
        Allowed strings are: ``RGB``, ``BGR``, ``GRAY``, ``CIE``, ``YCrCb``, ``HSV``, ``HLS``, ``Lab``, ``Luv``.
        These are also accessible via ``ChangeColorspace.<NAME>``, e.g. ``ChangeColorspace.YCrCb``.

            * If a string, it must be among the allowed colorspaces.
            * If a list, it is expected to be a list of strings, each one
              being an allowed colorspace. A random element from the list
              will be chosen per image.
            * If a StochasticParameter, it is expected to return string. A new
              sample will be drawn per image.

    from_colorspace : str, optional
        The source colorspace (of the input images).
        See `to_colorspace`. Only a single string is allowed.

    alpha : number or tuple of number or list of number or imgaug.parameters.StochasticParameter, optional
        The alpha value of the new colorspace when overlayed over the
        old one. A value close to 1.0 means that mostly the new
        colorspace is visible. A value close to 0.0 means, that mostly the
        old image is visible.

            * If an int or float, exactly that value will be used.
            * If a tuple ``(a, b)``, a random value from the range ``a <= x <= b`` will
              be sampled per image.
            * If a list, then a random value will be sampled from that list
              per image.
            * If a StochasticParameter, a value will be sampled from the
              parameter per image.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    """

    RGB = "RGB"
    BGR = "BGR"
    GRAY = "GRAY"
    CIE = "CIE"
    YCrCb = "YCrCb"
    HSV = "HSV"
    HLS = "HLS"
    Lab = "Lab"
    Luv = "Luv"
    COLORSPACES = {RGB, BGR, GRAY, CIE, YCrCb, HSV, HLS, Lab, Luv}
    # TODO access cv2 COLOR_ variables directly instead of indirectly via dictionary mapping
    CV_VARS = {
        # RGB
        "RGB2BGR": cv2.COLOR_RGB2BGR,
        "RGB2GRAY": cv2.COLOR_RGB2GRAY,
        "RGB2CIE": cv2.COLOR_RGB2XYZ,
        "RGB2YCrCb": cv2.COLOR_RGB2YCR_CB,
        "RGB2HSV": cv2.COLOR_RGB2HSV,
        "RGB2HLS": cv2.COLOR_RGB2HLS,
        "RGB2Lab": cv2.COLOR_RGB2LAB,
        "RGB2Luv": cv2.COLOR_RGB2LUV,
        # BGR
        "BGR2RGB": cv2.COLOR_BGR2RGB,
        "BGR2GRAY": cv2.COLOR_BGR2GRAY,
        "BGR2CIE": cv2.COLOR_BGR2XYZ,
        "BGR2YCrCb": cv2.COLOR_BGR2YCR_CB,
        "BGR2HSV": cv2.COLOR_BGR2HSV,
        "BGR2HLS": cv2.COLOR_BGR2HLS,
        "BGR2Lab": cv2.COLOR_BGR2LAB,
        "BGR2Luv": cv2.COLOR_BGR2LUV,
        # HSV
        "HSV2RGB": cv2.COLOR_HSV2RGB,
        "HSV2BGR": cv2.COLOR_HSV2BGR,
        # HLS
        "HLS2RGB": cv2.COLOR_HLS2RGB,
        "HLS2BGR": cv2.COLOR_HLS2BGR,
        # Lab
        "Lab2RGB": cv2.COLOR_Lab2RGB if hasattr(cv2, "COLOR_Lab2RGB") else cv2.COLOR_LAB2RGB,
        "Lab2BGR": cv2.COLOR_Lab2BGR if hasattr(cv2, "COLOR_Lab2BGR") else cv2.COLOR_LAB2BGR
    }

    def __init__(self, to_colorspace, from_colorspace="RGB", alpha=1.0, name=None, deterministic=False,
                 random_state=None):
        super(ChangeColorspace, self).__init__(name=name, deterministic=deterministic, random_state=random_state)

        # TODO somehow merge this with Alpha augmenter?
        self.alpha = iap.handle_continuous_param(alpha, "alpha", value_range=(0, 1.0), tuple_to_uniform=True,
                                                 list_to_choice=True)

        if ia.is_string(to_colorspace):
            ia.do_assert(to_colorspace in ChangeColorspace.COLORSPACES)
            self.to_colorspace = iap.Deterministic(to_colorspace)
        elif ia.is_iterable(to_colorspace):
            ia.do_assert(all([ia.is_string(colorspace) for colorspace in to_colorspace]))
            ia.do_assert(all([(colorspace in ChangeColorspace.COLORSPACES) for colorspace in to_colorspace]))
            self.to_colorspace = iap.Choice(to_colorspace)
        elif isinstance(to_colorspace, iap.StochasticParameter):
            self.to_colorspace = to_colorspace
        else:
            raise Exception("Expected to_colorspace to be string, list of strings or StochasticParameter, got %s." % (
                type(to_colorspace),))

        self.from_colorspace = from_colorspace
        ia.do_assert(self.from_colorspace in ChangeColorspace.COLORSPACES)
        ia.do_assert(from_colorspace != ChangeColorspace.GRAY)

        self.eps = 0.001  # epsilon value to check if alpha is close to 1.0 or 0.0

    def _augment_images(self, images, random_state, parents, hooks):
        result = images
        nb_images = len(images)
        alphas = self.alpha.draw_samples((nb_images,), random_state=ia.copy_random_state(random_state))
        to_colorspaces = self.to_colorspace.draw_samples((nb_images,), random_state=ia.copy_random_state(random_state))
        for i in sm.xrange(nb_images):
            alpha = alphas[i]
            to_colorspace = to_colorspaces[i]
            image = images[i]

            ia.do_assert(0.0 <= alpha <= 1.0)
            ia.do_assert(to_colorspace in ChangeColorspace.COLORSPACES)

            if alpha == 0 or self.from_colorspace == to_colorspace:
                pass  # no change necessary
            else:
                # some colorspaces here should use image/255.0 according to the docs,
                # but at least for conversion to grayscale that results in errors,
                # ie uint8 is expected

                if image.ndim != 3:
                    import warnings
                    warnings.warn(
                        "Received an image with %d dimensions in "
                        "ChangeColorspace._augment_image(), but expected 3 dimensions, i.e. shape "
                        "(height, width, channels)." % (image.ndim,)
                    )
                elif image.shape[2] != 3:
                    import warnings
                    warnings.warn(
                        "Received an image with shape (H, W, C) and C=%d in "
                        "ChangeColorspace._augment_image(). Expected C to usually be 3 -- any "
                        "other value will likely result in errors. (Note that this function is "
                        "e.g. called during grayscale conversion and hue/saturation "
                        "changes.)" % (image.shape[2],)
                    )

                if self.from_colorspace in [ChangeColorspace.RGB, ChangeColorspace.BGR]:
                    from_to_var_name = "%s2%s" % (self.from_colorspace, to_colorspace)
                    from_to_var = ChangeColorspace.CV_VARS[from_to_var_name]
                    img_to_cs = cv2.cvtColor(image, from_to_var)
                else:
                    # convert to RGB
                    from_to_var_name = "%s2%s" % (self.from_colorspace, ChangeColorspace.RGB)
                    from_to_var = ChangeColorspace.CV_VARS[from_to_var_name]
                    img_rgb = cv2.cvtColor(image, from_to_var)

                    if to_colorspace == ChangeColorspace.RGB:
                        img_to_cs = img_rgb
                    else:
                        # convert from RGB to desired target colorspace
                        from_to_var_name = "%s2%s" % (ChangeColorspace.RGB, to_colorspace)
                        from_to_var = ChangeColorspace.CV_VARS[from_to_var_name]
                        img_to_cs = cv2.cvtColor(img_rgb, from_to_var)

                # this will break colorspaces that have values outside 0-255 or 0.0-1.0
                # TODO dont convert to uint8
                if ia.is_integer_array(img_to_cs):
                    img_to_cs = np.clip(img_to_cs, 0, 255).astype(np.uint8)
                else:
                    img_to_cs = np.clip(img_to_cs * 255, 0, 255).astype(np.uint8)

                # for grayscale: covnert from (H, W) to (H, W, 3)
                if len(img_to_cs.shape) == 2:
                    img_to_cs = img_to_cs[:, :, np.newaxis]
                    img_to_cs = np.tile(img_to_cs, (1, 1, 3))

                result[i] = blend.blend_alpha(img_to_cs, image, alpha, self.eps)

        return images

    def _augment_heatmaps(self, heatmaps, random_state, parents, hooks):
        return heatmaps

    def _augment_keypoints(self, keypoints_on_images, random_state, parents, hooks):
        return keypoints_on_images

    def get_parameters(self):
        return [self.to_colorspace, self.alpha]


# TODO rename to Grayscale3D and add Grayscale that keeps the image at 1D?
def Grayscale(alpha=0, from_colorspace="RGB", name=None, deterministic=False, random_state=None):
    """
    Augmenter to convert images to their grayscale versions.

    NOTE: Number of output channels is still 3, i.e. this augmenter just "removes" color.

    TODO check dtype support

    dtype support::

        * ``uint8``: yes; fully tested
        * ``uint16``: ?
        * ``uint32``: ?
        * ``uint64``: ?
        * ``int8``: ?
        * ``int16``: ?
        * ``int32``: ?
        * ``int64``: ?
        * ``float16``: ?
        * ``float32``: ?
        * ``float64``: ?
        * ``float128``: ?
        * ``bool``: ?

    Parameters
    ----------
    alpha : number or tuple of number or list of number or imgaug.parameters.StochasticParameter, optional
        The alpha value of the grayscale image when overlayed over the
        old image. A value close to 1.0 means, that mostly the new grayscale
        image is visible. A value close to 0.0 means, that mostly the
        old image is visible.

            * If a number, exactly that value will always be used.
            * If a tuple ``(a, b)``, a random value from the range ``a <= x <= b`` will
              be sampled per image.
            * If a list, then a random value will be sampled from that list per image.
            * If a StochasticParameter, a value will be sampled from the
              parameter per image.

    from_colorspace : str, optional
        The source colorspace (of the input images).
        Allowed strings are: ``RGB``, ``BGR``, ``GRAY``, ``CIE``, ``YCrCb``, ``HSV``, ``HLS``, ``Lab``, ``Luv``.
        See :func:`imgaug.augmenters.color.ChangeColorspace.__init__`.

    name : None or str, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    deterministic : bool, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    random_state : None or int or numpy.random.RandomState, optional
        See :func:`imgaug.augmenters.meta.Augmenter.__init__`.

    Examples
    --------
    >>> aug = iaa.Grayscale(alpha=1.0)

    creates an augmenter that turns images to their grayscale versions.

    >>> aug = iaa.Grayscale(alpha=(0.0, 1.0))

    creates an augmenter that turns images to their grayscale versions with
    an alpha value in the range ``0 <= alpha <= 1``. An alpha value of 0.5 would
    mean, that the output image is 50 percent of the input image and 50
    percent of the grayscale image (i.e. 50 percent of color removed).

    """
    if name is None:
        name = "Unnamed%s" % (ia.caller_name(),)

    return ChangeColorspace(to_colorspace=ChangeColorspace.GRAY, alpha=alpha, from_colorspace=from_colorspace,
                            name=name, deterministic=deterministic, random_state=random_state)
