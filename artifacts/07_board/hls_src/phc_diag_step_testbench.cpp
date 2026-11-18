#include "phc_diag_step_hls.hpp"
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
static std::vector<std::string> split(const std::string& line) { std::vector<std::string> out; std::stringstream ss(line); std::string cell; while(std::getline(ss,cell,',')) out.push_back(cell); return out; }
static double number(const std::vector<std::string>& c,int i) { return std::strtod(c[i].c_str(),nullptr); }
static long long integer(const std::vector<std::string>& c,int i) { return std::strtoll(c[i].c_str(),nullptr,10); }
int main(int argc,char** argv) {
    if(argc<3) return 2; std::ifstream input(argv[1]); std::ofstream output(argv[2]); if(!input||!output) return 2;
    std::string line; std::getline(input,line); long long total=0,mismatch_rows=0,mismatch_elements=0,max_integer_diff=0;
    output<<"row_id,ref_quote_bid,dut_quote_bid,ref_quote_ask,dut_quote_ask,state_mismatch_elements,max_integer_diff,pass\n";
    while(std::getline(input,line)) {
        if(line.empty()) continue; auto c=split(line); if(c.size()<37) return 2;
        phc_fixed_t x[16],state_prev[8],state_next[8];
        for(int i=0;i<16;++i) x[i]=(phc_fixed_t)number(c,3+i); for(int i=0;i<8;++i) state_prev[i]=(phc_fixed_t)number(c,19+i);
        phc_packed_output_t packed=0; phc_h8_toxicity_seed1(x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11],x[12],x[13],x[14],x[15],state_prev[0],state_prev[1],state_prev[2],state_prev[3],state_prev[4],state_prev[5],state_prev[6],state_prev[7],packed);
        int ref_bid=(int)integer(c,27),ref_ask=(int)integer(c,28),dut_bid=(int)packed[0],dut_ask=(int)packed[1];
        long long row_bad=(ref_bid!=dut_bid)+(ref_ask!=dut_ask),row_max=0;
        for(int i=0;i<8;++i) { state_next[i].range(23,0)=packed.range(2+24*i+23,2+24*i); ap_int<24> bits=state_next[i].range(23,0); long long d=std::llabs(bits.to_int64()-integer(c,29+i)); row_bad+=d!=0; mismatch_elements+=d!=0; if(d>row_max)row_max=d; if(d>max_integer_diff)max_integer_diff=d; }
        mismatch_elements+=(ref_bid!=dut_bid)+(ref_ask!=dut_ask); mismatch_rows+=row_bad!=0;
        output<<total<<","<<ref_bid<<","<<dut_bid<<","<<ref_ask<<","<<dut_ask<<","<<row_bad<<","<<row_max<<","<<(row_bad==0)<<"\n"; ++total;
    }
    std::cout<<"total="<<total<<" mismatch_rows="<<mismatch_rows<<" mismatch_elements="<<mismatch_elements<<" max_integer_diff="<<max_integer_diff<<" unit=Q24.12_LSB\n";
    return mismatch_rows?1:0;
}
