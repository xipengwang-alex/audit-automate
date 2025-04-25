"""
Utilities for reporting and logging the status of product processing.
"""
import os
import time
from datetime import datetime, timedelta
import re

class AuditReport:
    """
    A class to track and report the status of product processing.
    """
    
    def __init__(self):
        """Initialize the report with empty dictionaries."""
        self.product_status = {}  # Maps product IDs to "Passed" or "Failed"
        self.status_details = {}  # Maps product IDs to status details (e.g., "missing Product Details")
        self.error_logs = {}      # Maps product IDs to error messages
        self.start_times = {}     # Maps product IDs to start times
        self.end_times = {}       # Maps product IDs to end times
        self.overall_start_time = time.time()  # Overall script start time
    
    def start_product(self, product_id):
        """
        Mark the start of processing for a product.
        
        Args:
            product_id: Identifier for the product (e.g., "link1")
        """
        self.start_times[product_id] = time.time()
        print(f"\n{'='*80}")
        print(f"STARTED PROCESSING: {product_id}")
        print(f"{'='*80}")
    
    def pass_product(self, product_id, details=None):
        """
        Mark a product as having passed processing.
        
        Args:
            product_id: Identifier for the product (e.g., "link1")
            details: Additional details about the status
        """
        self.product_status[product_id] = "Passed"
        if details:
            self.status_details[product_id] = details
        self.end_times[product_id] = time.time()
        duration = self.end_times[product_id] - self.start_times.get(product_id, self.end_times[product_id])
        
        print(f"\n{'-'*80}")
        status_text = f"PRODUCT {product_id}: PASSED"
        if details:
            status_text += f" w/ {details}"
        print(f"{status_text} (Duration: {duration:.2f}s)")
        print(f"{'-'*80}")
    
    def fail_product(self, product_id, error_message):
        """
        Mark a product as having failed processing.
        
        Args:
            product_id: Identifier for the product (e.g., "link1")
            error_message: The error message explaining the failure
        """
        self.product_status[product_id] = "Failed"
        self.error_logs[product_id] = error_message
        self.end_times[product_id] = time.time()
        duration = self.end_times[product_id] - self.start_times.get(product_id, self.end_times[product_id])
        
        print(f"\n{'-'*80}")
        print(f"PRODUCT {product_id}: FAILED (Duration: {duration:.2f}s)")
        print(f"Error: {error_message}")
        print(f"{'-'*80}")
    
    def print_summary(self):
        """Print a summary of all product processing results."""
        passed_count = sum(1 for status in self.product_status.values() if status == "Passed")
        failed_count = sum(1 for status in self.product_status.values() if status == "Failed")
        total_count = len(self.product_status)
        
        if total_count == 0:
            print("No products were processed.")
            return
        
        # Calculate total time
        total_time = time.time() - self.overall_start_time
        total_time_str = str(timedelta(seconds=int(total_time)))
        
        print(f"\n{'#'*80}")
        print(f"AUDIT REPORT SUMMARY")
        print(f"{'#'*80}")
        print(f"Total Products: {total_count}")
        print(f"Passed: {passed_count} ({passed_count/total_count*100:.1f}%)")
        print(f"Failed: {failed_count} ({failed_count/total_count*100:.1f}%)")
        print(f"Total Time: {total_time_str}")
        print(f"{'#'*80}")
        
        # Print individual product statuses
        print("\nDETAILED RESULTS:")
        for product_id in sorted(self.product_status.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
            status = self.product_status[product_id]
            if status == "Failed":
                error = self.error_logs.get(product_id, "Unknown error")
                print(f"Product {product_id}: {status} - {error}")
            else:
                details = f" w/ {self.status_details[product_id]}" if product_id in self.status_details else ""
                print(f"Product {product_id}: {status}{details}")
        
        print(f"{'#'*80}\n")
    
    def save_report(self, output_folder="output"):
        """
        Save the report to a file in the audit_report folder.
        
        Args:
            output_folder: Base folder for outputs (reports will go in a subfolder)
            
        Returns:
            str: Path to the saved report file
        """
        # Create audit_report folder inside the output folder
        report_folder = os.path.join(output_folder, "audit_report")
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)
        
        # Create a Windows-safe timestamp (no colons)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_folder, f"audit_report_{timestamp}.txt")
        
        # Calculate total time
        total_time = time.time() - self.overall_start_time
        total_time_str = str(timedelta(seconds=int(total_time)))
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"APEC WATER AUDIT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n\n")
                
                # Summary statistics
                passed_count = sum(1 for status in self.product_status.values() if status == "Passed")
                failed_count = sum(1 for status in self.product_status.values() if status == "Failed")
                total_count = len(self.product_status)
                
                if total_count == 0:
                    f.write("No products were processed.\n")
                    print(f"Report saved to: {report_file}")
                    return report_file
                
                f.write(f"SUMMARY:\n")
                f.write(f"Total Products: {total_count}\n")
                f.write(f"Passed: {passed_count} ({passed_count/total_count*100:.1f}%)\n")
                f.write(f"Failed: {failed_count} ({failed_count/total_count*100:.1f}%)\n")
                f.write(f"Total Time: {total_time_str}\n\n")
                
                # Detailed results
                f.write(f"DETAILED RESULTS:\n")
                f.write(f"{'-'*80}\n")
                for product_id in sorted(self.product_status.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
                    status = self.product_status[product_id]
                    if status == "Failed":
                        error = self.error_logs.get(product_id, "Unknown error")
                        f.write(f"Product {product_id}: {status}\n")
                        f.write(f"Error: {error}\n\n")
                    else:
                        details = f" w/ {self.status_details[product_id]}" if product_id in self.status_details else ""
                        f.write(f"Product {product_id}: {status}{details}\n\n")
                
                f.write(f"{'='*80}\n")
                f.write(f"End of Report\n")
            
            print(f"Report saved to: {report_file}")
            return report_file
            
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            # Return a fallback filename if there was an error
            return os.path.join(report_folder, "audit_report.txt")

# Global report instance
report = AuditReport()