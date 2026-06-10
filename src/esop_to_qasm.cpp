#include <caterpillar/synthesis/stg_to_mcx.hpp>
#include <caterpillar/synthesis/lhrs.hpp>
#include <caterpillar/structures/stg_gate.hpp>
#include <caterpillar/synthesis/strategies/xag_mapping_strategy.hpp>
#include <caterpillar/synthesis/strategies/pebbling_mapping_strategy.hpp>

#include <kitty/constructors.hpp>
#include <kitty/dynamic_truth_table.hpp>

#include <tweedledum/io/qasm.hpp>
#include <tweedledum/gates/gate_set.hpp>
#include <tweedledum/networks/netlist.hpp>
#include <tweedledum/algorithms/decomposition/dt.hpp>
#include <tweedledum/algorithms/decomposition/barenco.hpp>
#include <tweedledum/gates/mcst_gate.hpp>
#include <tweedledum/io/write_projectq.hpp>

#include <mockturtle/networks/xag.hpp>
#include <mockturtle/algorithms/node_resynthesis/shannon.hpp> // shannon_resynthesis
#include <mockturtle/algorithms/node_resynthesis/davio.hpp> // shannon_resynthesis
#include <mockturtle/algorithms/node_resynthesis/xag_minmc2.hpp>
#include <mockturtle/algorithms/cut_rewriting.hpp>
#include <mockturtle/properties/mccost.hpp>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/io/write_blif.hpp>

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

// Find max variable letter used in the expression (a..p) to size the truth table.
static uint32_t infer_num_vars(std::string const& expr) {
  char maxv = 0;
  for (char c : expr) {
    if (c >= 'a' && c <= 'p') {
      if (c > maxv) maxv = c;
    }
  }
  if (maxv == 0) return 0;
  return static_cast<uint32_t>(maxv - 'a' + 1);
}

static void usage(char const* argv0) {
  std::cerr
    << "Usage:\n"
    << "  " << argv0 << " '<kitty-expr>' out.qasm\n\n"
    << "Kitty expression syntax:\n"
    << "  vars: a..p\n"
    << "  NOT:  !E\n"
    << "  AND:  (E...E)\n"
    << "  OR:   {E...E}\n"
    << "  XOR:  [E...E]\n\n"
    << "Example:\n"
    << "  " << argv0 << " '[a(bc)]' out.qasm\n"
    << "    means: a XOR (b AND c)\n";
}

int main(int argc, char** argv) {
  if (argc != 3) {
    usage(argv[0]);
    return 2;
  }

  std::string const expr = argv[1];
  std::string const out_qasm = argv[2];

  uint32_t const n = infer_num_vars(expr);
  if (n == 0) {
    std::cerr << "[e] no variables a..p found in expression\n";
    return 1;
  }

  // 1) Parse expression -> truth table
  kitty::dynamic_truth_table tt(n);
  if (!kitty::create_from_expression(tt, expr)) {
    std::cerr << "[e] failed to parse expression\n";
    return 1;
  }
  mockturtle::xag_network xag;

  // Create leaves (PIs)
  std::vector<mockturtle::xag_network::signal> leaves;
  for ( auto i = 0u; i < tt.num_vars(); ++i )
    leaves.push_back( xag.create_pi() );


  mockturtle::positive_davio_resynthesis<mockturtle::xag_network> resyn;
  resyn( xag, tt, leaves.begin(), leaves.end(),
         [&]( mockturtle::xag_network::signal const& f ) {
           xag.create_po( f );
         } );

  
  // Resynthesize into the network
  mockturtle::future::xag_minmc_resynthesis optsyn;
  mockturtle::write_blif(xag, "before.blif"); // DCDEBUG
  mockturtle::cut_rewriting_with_compatibility_graph( xag, optsyn, {},
						      nullptr, mockturtle::mc_cost<mockturtle::xag_network>() );

  xag = mockturtle::cleanup_dangling( xag );
  mockturtle::write_blif(xag, "out.blif"); // DCDEBUG
  
  
  // 2) Synthesize reversible network from ESOP (ESOP extracted internally from tt)
  //    The stg_from_exact_synthesis synthesizes an ESOP then maps cubes to MCX
  //    on a dedicated target qubit (last element in qubit_map).
  // caterpillar::stg_from_exact_synthesis synth;

  // tweedledum::netlist<caterpillar::stg_gate> net;
  // for (uint32_t i = 0; i < n + 1; i++) {
  //   net.add_qubit();
  // }

  // std::vector<tweedledum::qubit_id> qubit_map(n + 1);

  // for (uint32_t i = 0; i < n + 1; ++i) {
  //   qubit_map[i] = tweedledum::qubit_id(i);
  // }
  // synth(net, qubit_map, tt);


  /* select the pebbling compilation strategy */
  caterpillar::pebbling_mapping_strategy_params ps;
  ps.pebble_limit = 100;

  //caterpillar::pebbling_mapping_strategy<mockturtle::xag_network> strategy( ps );
  // caterpillar::pebbling_mapping_strategy<
  //   mockturtle::xag_network,
  //   caterpillar::z3_pebble_solver<mockturtle::xag_network>
  //   > strategy( ps );

  caterpillar::xag_pebbling_mapping_strategy strategy;
  /* compile to quantum circuit */
  tweedledum::netlist<caterpillar::stg_gate> circ;

  caterpillar::logic_network_synthesis( circ, xag, strategy);
  tweedledum::write_projectq(circ, "net_projectq.py");
  // tweedledum::netlist<tweedledum::mcst_gate> decomposed;
  // for (uint32_t i = 0; i < 2 * n + 1; i++) {
  //   decomposed.add_qubit();
  // }
  // tweedledum::dt_decomposition(decomposed, net);
  
  // 3) Write OpenQASM 2.0
  auto decomposed = tweedledum::barenco_decomposition(circ);

  tweedledum::write_projectq(decomposed, "decomposed_projectq.py");
  //auto decomposed = circ;
  
  std::ofstream os("out.qasm");
  tweedledum::write_qasm(decomposed, os);

  std::cout << "[i] wrote " << out_qasm << " (qubits=" << decomposed.num_qubits()
            << ", gates synthesized)\n";
  return 0;
}
