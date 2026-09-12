import TimeWarp

open TimeWarp

-- Every headline result, checked for the axioms it depends on.
#print axioms TimeWarp.disc_self
#print axioms TimeWarp.disc_comm
#print axioms TimeWarp.disc_triangle
#print axioms TimeWarp.disc_le_of_mem_Icc
#print axioms TimeWarp.coverage
#print axioms TimeWarp.coverage_min_antitone
#print axioms TimeWarp.coverage_min_eq_of_mem
#print axioms TimeWarp.coverage_empty_false
#print axioms TimeWarp.coverage_average_not_antitone
#print axioms TimeWarp.hoeffding_mean_ge
#print axioms TimeWarp.hoeffding_mean_le
#print axioms TimeWarp.exp_hoeffding_calibrated
#print axioms TimeWarp.across_versions
#print axioms TimeWarp.across_versions_rev
#print axioms TimeWarp.within_versions
#print axioms TimeWarp.within_versions_rev
#print axioms TimeWarp.exp_eps1
#print axioms TimeWarp.exp_eps2
#print axioms TimeWarp.real_badEvent_le
#print axioms TimeWarp.versionCount
#print axioms TimeWarp.eps1_one
#print axioms TimeWarp.single_version_floor
#print axioms TimeWarp.eps2_of_budget
#print axioms TimeWarp.eps1_antitone
#print axioms TimeWarp.fixed_budget
#print axioms TimeWarp.coverage_seq
#print axioms TimeWarp.coverage_pooled_le
#print axioms TimeWarp.pooled_set_ne_pooled_seq
#print axioms TimeWarp.prob_le_actionProb
#print axioms TimeWarp.prob_eq_actionProb_iff
#print axioms TimeWarp.bcLoss_le_twbcLoss
#print axioms TimeWarp.bcLoss_lt_twbcLoss_example
