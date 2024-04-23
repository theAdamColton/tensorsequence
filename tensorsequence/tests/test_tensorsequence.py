import unittest
import torch
from ..tensorsequence import TensorSequence, TensorSet


class TestTensorSet(unittest.TestCase):
    def test_validate_input_columns(self):
        def assert_value_error(do):
            occurred = False
            try:
                do()
            except ValueError:
                occurred = True
            self.assertTrue(occurred, "value error did not occurr as expected")

        c1 = torch.randn(3, 7, 9)
        c2 = torch.randn(3, 10, 3)

        # incompatible along dim 1
        assert_value_error(lambda: TensorSequence([c1, c2], sequence_dim=1))
        assert_value_error(lambda: TensorSequence([c1], {"c2": c2}, sequence_dim=1))

        # fine along dim 0
        TensorSequence([c1, c2], sequence_dim=0)
        TensorSequence([c1], {"c2": c2}, sequence_dim=0)

    def test_stack(self):
        c1 = torch.randn(7, 5, 3, 1, 1, 1)
        c2 = torch.randn(7, 5, 3, 4)
        c3 = torch.randn(7, 5, 3) > 0

        ts = TensorSequence([c1, c2], {"c3": c3}, 2)

        self.assertEqual(ts.sequence_length, 3)
        self.assertEqual(ts.leading_shape, (7, 5, 3))

        stacked = TensorSequence.stack([ts, ts, ts])

        self.assertEqual(3, stacked.sequence_dim)
        self.assertEqual((3, 7, 5, 3), stacked.leading_shape)

    def test_iloc_dim0(self):
        c0 = torch.randn(10, 100)
        c1 = torch.randn(10, 100, 7)
        ts = TensorSequence([c0, c1], sequence_dim=1)

        ts0 = ts.iloc[0]

        self.assertIsInstance(ts0, TensorSet)
        self.assertTrue(torch.equal(ts0.columns[0], c0[0]))

    def test_iloc_dim1(self):
        # batch, channel, sequence, z
        c0 = torch.randn(3, 2, 100)
        c1 = torch.randn(3, 2, 100, 4)
        ts = TensorSequence([c0, c1], sequence_dim=2)
        self.assertEqual(ts.sequence_length, 100)

        ts0 = ts.iloc[0]

        self.assertIsInstance(ts0, TensorSet)
        self.assertTrue(torch.equal(ts0.columns[0], c0[0]))
        self.assertTrue(torch.equal(ts0.columns[1], c1[0]))

        ts2 = ts.iloc[2]

        self.assertIsInstance(ts2, TensorSet)
        self.assertTrue(torch.equal(ts2.columns[0], c0[2]))
        self.assertTrue(torch.equal(ts2.columns[1], c1[2]))

    def test_index_column(self):
        c0 = torch.randn(2, 55)
        c1 = torch.randn(2, 55, 3)
        ts = TensorSequence([c0, c1], sequence_dim=1)
        self.assertTrue(torch.equal(c0, ts[0]))
        self.assertTrue(torch.equal(c1, ts[1]))

    def test_index_column_by_name(self):
        c0 = torch.randn(2, 55)
        c1 = torch.randn(2, 55, 3)
        ts = TensorSequence(named_columns=dict(c1=c0, c2=c1), sequence_dim=1)
        self.assertTrue(torch.equal(c0, ts["c1"]))
        self.assertTrue(torch.equal(c1, ts["c2"]))

    def test_cat(self):
        c11 = torch.randn(2, 7)
        c21 = torch.randn(2, 7, 5)
        ts1 = TensorSequence((c11, c21), sequence_dim=1)

        c12 = torch.randn(2, 32)
        c22 = torch.randn(2, 32, 5)
        ts2 = TensorSequence((c12, c22), sequence_dim=1)

        tscat = TensorSequence.cat((ts1, ts2))
        self.assertTrue(torch.equal(torch.cat((c11, c12), 1), tscat[0]))
        self.assertTrue(torch.equal(torch.cat((c21, c22), 1), tscat[1]))

    def test_pad_value(self):
        c0 = torch.zeros(10, 1)
        c1 = torch.zeros(10, 1, 7)
        ts = TensorSequence((c0, c1), sequence_dim=1)
        padded = ts.pad(15, 1.0)
        self.assertEqual(padded.sequence_length, 16)
        self.assertTrue(torch.all(padded[0][:, 1:] == 1.0))
        self.assertTrue(torch.all(padded[1][:, 1:] == 1.0))

    def test_pad_value_dict(self):
        c0 = torch.zeros(8, 3)
        c1 = torch.zeros(8, 3, 1)
        ts = TensorSequence(named_columns=dict(c1=c0, c2=c1), sequence_dim=1)
        padded = ts.pad(17, value_dict=dict(c1=1.0, c2=2.0))
        self.assertEqual(padded.sequence_length, 20)
        self.assertTrue(torch.all(padded["c1"][:, 3:] == 1.0))
        self.assertTrue(torch.all(padded["c2"][:, 3:] == 2.0))

    def test_to_device(self):
        c0 = torch.zeros(8, 3)
        c1 = torch.zeros(8, 3, 1)
        ts = TensorSequence(named_columns=dict(c1=c0, c2=c1), sequence_dim=1)
        self.assertEqual((8, 3), ts.leading_shape)
        self.assertEqual(3, ts.sequence_length)
        self.assertEqual(1, ts.sequence_dim)
        ts = ts.to_device("cpu")
        self.assertEqual((8, 3), ts.leading_shape)
        self.assertEqual(3, ts.sequence_length)
        self.assertEqual(1, ts.sequence_dim)
