#pragma once
#include <ap_fixed.h>
#include <ap_int.h>

typedef ap_fixed<24, 12, AP_TRN, AP_SAT> phc_fixed_t;
typedef ap_fixed<40, 16, AP_TRN, AP_SAT> phc_acc_t;
typedef ap_fixed<48, 24, AP_TRN, AP_SAT> phc_var_t;
typedef ap_fixed<18, 12, AP_TRN, AP_SAT> phc_input_mult_t;
typedef ap_fixed<18, 4, AP_TRN, AP_SAT> phc_fold_weight_mult_t;
typedef ap_fixed<18, 4, AP_TRN, AP_SAT> phc_fold_bias_mult_t;
typedef ap_fixed<18, 3, AP_TRN, AP_SAT> phc_gamma_mult_t;
typedef ap_fixed<18, 2, AP_TRN, AP_SAT> phc_beta_mult_t;
typedef ap_fixed<18, 2, AP_TRN, AP_SAT> phc_decay_mult_t;
typedef ap_fixed<18, 1, AP_TRN, AP_SAT> phc_gain_mult_t;
typedef ap_fixed<18, 2, AP_TRN, AP_SAT> phc_readout_mult_t;
typedef ap_fixed<18, 1, AP_TRN, AP_SAT> phc_readout_bias_mult_t;
typedef ap_fixed<18, 3, AP_TRN, AP_SAT> phc_weight_mult_t;
typedef ap_fixed<18, 2, AP_TRN, AP_SAT> phc_inv_norm_t;
typedef ap_fixed<18, 5, AP_TRN, AP_SAT> phc_hidden_mult_t;
typedef ap_fixed<14, 5, AP_TRN, AP_SAT> phc_scale_guard_t;
static const int PHC_FEATURE_DIM = 16;
static const int PHC_HIDDEN_DIM = 8;
static const int PHC_READOUT_DIM = 2;
typedef ap_uint<194> phc_packed_output_t;

void phc_h8_toxicity_seed1(
    const phc_fixed_t x0,
    const phc_fixed_t x1,
    const phc_fixed_t x2,
    const phc_fixed_t x3,
    const phc_fixed_t x4,
    const phc_fixed_t x5,
    const phc_fixed_t x6,
    const phc_fixed_t x7,
    const phc_fixed_t x8,
    const phc_fixed_t x9,
    const phc_fixed_t x10,
    const phc_fixed_t x11,
    const phc_fixed_t x12,
    const phc_fixed_t x13,
    const phc_fixed_t x14,
    const phc_fixed_t x15,
    const phc_fixed_t state_prev0,
    const phc_fixed_t state_prev1,
    const phc_fixed_t state_prev2,
    const phc_fixed_t state_prev3,
    const phc_fixed_t state_prev4,
    const phc_fixed_t state_prev5,
    const phc_fixed_t state_prev6,
    const phc_fixed_t state_prev7,
    phc_packed_output_t& packed_output
);
