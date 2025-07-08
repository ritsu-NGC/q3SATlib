#ifndef EXORCISM_H
#define EXORCISM_H

#include <cstdint>
#include <functional>
#include "eabc/exor.h"
/**
 * Abc_ExorcismMain
 *  Minimizes an ESOP (Exclusive Sum-Of-Products) cover.
 *
 * @param vEsop       Pointer to ESOP cube set (may be nullptr for demo purposes)
 * @param nIns        Number of input variables
 * @param nOuts       Number of output variables
 * @param onCube      Callback for each output cube: void(uint32_t bits, uint32_t mask)
 * @param Quality     Quality parameter
 * @param Verbosity   Verbosity level
 * @param nCubesMax   Maximum number of cubes allowed
 * @param fUseQCost   Use QCost metric if nonzero
 * @return            1 on success, 0 on failure
 */

namespace abc {
  namespace exorcism {
    int Abc_ExorcismMain(
		Vec_Wec_t * vEsop,
		int nIns,
		int nOuts,
		const std::function<void(uint32_t, uint32_t)>& onCube,
		int Quality,
		int Verbosity,
		int nCubesMax,
		int fUseQCost
		);
  }
}

#endif // EXORCISM_H
