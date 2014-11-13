//=================================================================================================
//  GANDALF :
//  Graphical Astrophysics code for N-body Dynamics And Lagrangian Fluids
//  https://github.com/gandalfcode/gandalf
//  Contact : gandalfcode@gmail.com
//
//  Copyright (C) 2013  D. A. Hubber, G. Rosotti
//
//  GANDALF is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 2 of the License, or
//  (at your option) any later version.
//
//  GANDALF is distributed in the hope that it will be useful, but
//  WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//  General Public License (http://www.gnu.org/licenses) for more details.
//=================================================================================================


#include <fstream>
#include <iostream>
#include <string>
#include <sstream>
#include "Exception.h"
#include "Parameters.h"
#include "Simulation.h"
#include "CodeTiming.h"
#ifdef MPI_PARALLEL
#include "mpi.h"
#endif
using namespace std;



//=================================================================================================
//  main
/// Main GANDALF program for running executables from the command line.
//=================================================================================================
int main(int argc, char** argv)
{
  bool restart=false;                                // Flag restart simulation
  int rank=0;                                        // Local copy of MPI rank
  string paramfile;                                  // Name of parameters file
  stringstream ss;                                   // Stream char to string
  ofstream outfile;                                  // Stream of temp restart file
  CodeTiming* timing = new CodeTiming();             // Timing object
  SimulationBase* sim;                               // Main simulation object
  Parameters* params = new Parameters();             // Parameters object
  ExceptionHandler::makeExceptionHandler(cplusplus); // Exception handler


#ifdef MPI_PARALLEL
  // Initialise all MPI processes (if activated in Makefile)
  MPI_Init(&argc,&argv);
  MPI_Comm_rank(MPI_COMM_WORLD,&rank);

  // Tell exception handler to call MPI_Abort on error
  ExceptionHandler::set_mpi(1);

#ifdef _OPENMP
  // Check that OpenMP and MPI can work together
  int mpi_thread_support;
  MPI_Query_thread(&mpi_thread_support);
  if (mpi_thread_support == MPI_THREAD_SINGLE)
    ExceptionHandler::getIstance().raise("This implementation of MPI is not interoperable with OpenMP, aborting!"
        "Refer to your system administrator to know how to solve this problem");
#endif
#endif


  // Parse and process all command-line arguments.
  if (argc == 3) {
    if (string(argv[1]) == "-r") {
      restart = true;
      ss << argv[2];
      ss >> paramfile;
    }
  }
  else if (argc == 2) {
    paramfile = string(argv[1]);
  }
  else {
    cout << "No parameter file specified, aborting..." << endl;
    exit(-1);
  }

  // Create empty file (used for automatic restarts on clusters)
  outfile.open("cont");
  outfile.close();

  // Read parameters file immediately and record to file
  params->ReadParamsFile(paramfile);
  params->RecordParametersToFile();

  // Create simulation object with required dimensionality and parameters
  sim = SimulationBase::SimulationFactory(params->intparams["ndim"],
                                          params->stringparams["sim"],params);
  sim->timing = timing;
  sim->restart = restart;

  // Print out splash screen
  if (rank == 0) sim->SplashScreen();

  // Perform all set-up procedures
  sim->SetupSimulation();

  // Run entire simulation until specified end-time in parameters file.
  sim->Run();

#ifdef MPI_PARALLEL
  MPI_Finalize();
#endif

  // Compile timing statistics from complete simulation
  timing->ComputeTimingStatistics(sim->run_id);

  return 0;
}
